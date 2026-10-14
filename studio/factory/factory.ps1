<#
Crazy Facts factory: one queue, many agents, one style.
  factory.ps1 controller            planner + watchdog + git hand-off (one per machine)
  factory.ps1 worker -Name codex1   pulls tasks it may do, runs its agent headless, validates, records tokens
  factory.ps1 dash                  live overview of agents, queue, pipelines, tokens, alerts
  factory.ps1 status                one-shot overview
  factory.ps1 new-video             start a video pipeline now (ignores the watermarks)
  factory.ps1 enqueue -Type cf_audit -Arg '{"block":"lf12_b03"}'
  factory.ps1 add-agent -Name codex3 -Kind codex [-Model sonnet]
  factory.ps1 pause | resume | retry -Id <task> | kill -Id <task>
State (queue, heartbeats, metrics) lives in studio/factory/state (not committed). Content lives in the repo.
#>
param([Parameter(Position = 0)][string]$Mode = 'status', [string]$Name, [string]$Kind, [string]$Model, [string]$Type, [string]$Arg = '{}', [string]$Id)
$ErrorActionPreference = 'Stop'
$F = $PSScriptRoot; $Repo = (Resolve-Path "$F\..\..").Path; $S = "$F\state"; $AE = "$Repo\studio\assetedit"
foreach ($d in 'queue\pending', 'queue\active', 'queue\done', 'queue\failed', 'agents', 'runs', 'kill', 'inbox', 'pipelines', 'out', '..\scripts', '..\render') { New-Item -ItemType Directory -Force "$S\$d" | Out-Null }
$Utf8 = New-Object Text.UTF8Encoding $false
$Git = 'C:\Program Files\Git\cmd\git.exe'
$HerdrExe = (Get-Command herdr -ErrorAction SilentlyContinue).Source; if (-not $HerdrExe) { $HerdrExe = "$env:USERPROFILE\.herdr\packages\standalone\current\herdr.exe" }
$Exe = @{
  codex  = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\OpenAI.Codex_Microsoft.Winget.Source_8wekyb3d8bbwe\codex.exe"
  claude = @((Get-Command claude -ErrorAction SilentlyContinue).Source, "$env:USERPROFILE\.local\bin\claude.exe" | Where-Object { $_ -and (Test-Path $_) })[0]
  copilot = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\GitHub.Copilot_Microsoft.Winget.Source_8wekyb3d8bbwe\copilot.exe"
}

# ---------- small helpers ----------
function Now { [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() }
function Today { (Get-Date).ToString('yyyy-MM-dd') }
function RJ($p) { if (Test-Path $p) { Get-Content $p -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable } }
function WJ($p, $o) { [IO.File]::WriteAllText($p, ($o | ConvertTo-Json -Depth 30), $Utf8) }
function WT($p, $t) { [IO.File]::WriteAllText($p, $t, $Utf8) }
function Cfg { RJ "$F\config.json" }
function Agents { @(RJ "$F\agents.json") }
function Ctl { $c = RJ "$S\control.json"; if (-not $c) { $c = [ordered]@{ paused = $false; cf_mode = 'generating'; started = @{}; last_pull = 0; last_analyze = 0; analyze_hash = '' } }; $c }
function SaveCtl($c) { WJ "$S\control.json" $c }
function Ev($h) { $h.ts = Now; [IO.File]::AppendAllText("$S\events.jsonl", ($h | ConvertTo-Json -Compress -Depth 10) + "`n", $Utf8) }
function Fmt($s) { if ($s -lt 60) { "{0}s" -f [int]$s } elseif ($s -lt 3600) { "{0}m{1:00}s" -f [math]::Floor($s / 60), ($s % 60) } else { "{0}h{1:00}m" -f [math]::Floor($s / 3600), [math]::Floor(($s % 3600) / 60) } }
function Num($n) { if ($n -ge 1e6) { "{0:0.0}M" -f ($n / 1e6) } elseif ($n -ge 1e3) { "{0:0.0}k" -f ($n / 1e3) } else { "$n" } }
function Lock([scriptblock]$sb) {
  for ($i = 0; $i -lt 600; $i++) { try { $fs = [IO.File]::Open("$S\lock", 'OpenOrCreate', 'ReadWrite', 'None'); break } catch { Start-Sleep -Milliseconds 100 } }
  try { & $sb } finally { if ($fs) { $fs.Dispose() } }
}
function Herdr { param([Parameter(ValueFromRemainingArguments)]$a) try { $o = & $HerdrExe @a 2>$null; if ($o) { ($o -join "`n") | ConvertFrom-Json -AsHashtable -ErrorAction SilentlyContinue } } catch {} }
function Notify($title, $body) { if (Test-Path $HerdrExe) { Herdr notification show $title --body $body --position top-right --sound request | Out-Null } }

# ---------- queue ----------
function TPath($id) { foreach ($q in 'pending', 'active', 'done', 'failed') { $p = "$S\queue\$q\$id.json"; if (Test-Path $p) { return $p } } }
function Tasks($q) { @(Get-ChildItem "$S\queue\$q" -Filter *.json -ErrorAction SilentlyContinue | ForEach-Object { $t = RJ $_.FullName; if ($t) { $t } }) }
function Ensure($type, $key, $targs, $deps, $pipeline) {
  $id = "$type-$key"; if (TPath $id) { return $id }
  $c = Cfg; $t = [ordered]@{ id = $id; type = $type; args = $targs; deps = @($deps); pipeline = $pipeline; priority = $c.types[$type].priority; created = Now; queued = Now; attempts = 0; avoid = @(); history = @() }
  WJ "$S\queue\pending\$id.json" $t; Ev @{ ev = 'queued'; task = $id; type = $type }; $id
}
function Done($id) { Test-Path "$S\queue\done\$id.json" }
function Requeue($t, $from, $agent, $why) {
  $c = Cfg; $t.attempts++; if ($agent -and $t.avoid -notcontains $agent) { $t.avoid += $agent }
  $t.history += "$(Get-Date -f 'MM-dd HH:mm') $agent $why"; $t.queued = Now; $t.Remove('agent'); $t.Remove('started')
  $to = if ($t.attempts -ge $c.max_attempts) { 'failed' } else { 'pending' }
  WJ "$S\queue\$to\$($t.id).json" $t; Remove-Item $from -ErrorAction SilentlyContinue
  Ev @{ ev = $(if ($to -eq 'failed') { 'failed' } else { 'requeued' }); task = $t.id; type = $t.type; agent = $agent; why = $why }
  if ($to -eq 'failed') { Notify "Factory: task failed" "$($t.id): $why" }
}

# ---------- agent state ----------
function AState($n) { $a = RJ "$S\agents\$n.json"; if (-not $a) { $a = [ordered]@{ name = $n } }; if ($a.day -ne (Today)) { $a.day = Today; $a.done = 0; $a.failed = 0; $a.tin = 0; $a.tout = 0; $a.cached = 0; $a.cost = 0.0; $a.busy = 0 }; $a }
function SaveA($a) { $a.hb = Now; WJ "$S\agents\$($a.name).json" $a }
function Alive($n) { $a = RJ "$S\agents\$n.json"; $a -and ((Now) - $a.hb) -lt (Cfg).heartbeat_stale_s -and $a.state -notin 'cooldown', 'disabled', 'offline', 'capped' }

# ---------- shared context pack (the "one brain") ----------
function Section($file, $head) { if (-not (Test-Path $file)) { return '' }; $t = Get-Content $file -Raw -Encoding utf8; $i = $t.IndexOf($head); if ($i -lt 0) { return '' }; $r = $t.Substring($i + $head.Length); $j = $r.IndexOf("`n## "); if ($j -ge 0) { $r = $r.Substring(0, $j) }; $r.Trim() }
function Manifest { $m = RJ "$AE\manifest.json"; $sp = @{}; foreach ($a in $m.assets) { if ($a.approved) { $sp[$a.asset_id] = $a.emotion } }; $bg = @{}; foreach ($b in $m.backgrounds) { if ($b.approved) { $bg[$b.bg_id] = @($b.emotions) } }; @{ sp = $sp; bg = $bg } }
function VideoMeta { @(Get-ChildItem "$AE\videos" -Filter 'lf??.json' | Sort-Object Name | ForEach-Object { RJ $_.FullName }) }
function Pack {
  $m = Manifest; $vids = VideoMeta
  $recent = ($vids | Select-Object -Last 6 | ForEach-Object { $th = $_.thumb; "- $($_.id) `"$($_.title)`" format $($_.format) | thumb `"$($th.text)`" sprite $($th.sprite) bg $($th.bg) accent $($th.accent) mirror $([bool]$th.mirror) | playlist $(@($_.playlists)[0])" }) -join "`n"
  $titles = (@(RJ "$AE\videos\series.json") | ForEach-Object { $_.title }) -join ' | '
  $byEmo = $m.sp.GetEnumerator() | Group-Object Value | Sort-Object Name | ForEach-Object { "$($_.Name): " + (($_.Group | ForEach-Object Key | Sort-Object) -join ' ') }
  $bgs = $m.bg.GetEnumerator() | Sort-Object Key | ForEach-Object { "$($_.Key) [$($_.Value -join ',')]" }
  $ins = Get-Content "$Repo\studio\insights.md" -Raw -Encoding utf8; $blocks = $ins -split "`n(?=## )"; $ins = ($blocks | Select-Object -Last 2) -join "`n"
  $txt = @"
# CONTEXT PACK: read fully before producing anything. You are one of several agents acting as ONE editor.
$(Get-Content "$F\STYLE.md" -Raw -Encoding utf8)

# LEARNED RULES (from real performance, shared by all agents)
$(Section "$F\learned.md" '## Rules')

# LESSONS (problems found in published videos; every rule applies)
$(Section "$Repo\studio\lessons.md" '## Rules')

# TREND RULES (outside channels; our own numbers win when they disagree)
$(Section "$Repo\studio\trends.md" '## Rules')

# OUR NUMBERS (latest insights)
$ins

# RECENT VIDEOS (variety: differ from the last two)
$recent

# PLANNED/USED TITLES (never repeat a topic)
$titles

# APPROVED SPRITES BY EMOTION (prefix = character family; A = the red-hoodie chibi)
$($byEmo -join "`n")

# APPROVED BACKGROUNDS [allowed sprite emotions]
$($bgs -join "`n")
"@
  $h = [BitConverter]::ToString([Security.Cryptography.SHA1]::Create().ComputeHash($Utf8.GetBytes($txt))).Replace('-', '').Substring(0, 8).ToLower()
  WT "$S\pack.md" $txt; WT "$S\pack.hash" $h; @{ hash = $h; text = $txt }
}

# ---------- validators ----------
function Segs($text) { @(($text -replace "`r", '') -split "\n\s*\n" | Where-Object { $_.Trim() } | ForEach-Object { , @($_ -split "`n" | Where-Object { $_.Trim() }) }) }
function CheckBlock($text, $bid) {
  $m = Manifest; $e = @(); $ai = @(); $run = 0; $n = 0; $photos = 0; $words = 0
  $need = @{ list = 2; study = 3; stat = 3; bars = 3; quote = 2; curve = 5; chapter = 1; end = 1 }
  foreach ($L in (Segs $text)) { if ($L[0].StartsWith('#')) { foreach ($l in $L) { if ($l -match '^#(ai|ov) (\S+) \| .+') { $ai += $Matches[2] } else { $e += "bad image line: $l" } } } }
  foreach ($L in (Segs $text)) {
    if ($L[0].StartsWith('#')) { continue }
    $n++; $h = $L[0].Trim(); $say = ($L | Select-Object -Skip 1) -join ' '
    if (-not $say.Trim()) { $e += "seg ${n}: empty voice line ($h)" }
    $words += ($say -split '\s+' | Where-Object { $_ }).Count
    if ($say -match '\b[Pp]art (one|two|three|\d+)\b|\[\d\d:\d\d') { $e += "seg ${n}: part numbers/timestamps in the voice line" }
    if ($h -notmatch '^@(char|chapter|end|list|study|stat|bars|quote|curve|photo)\s+(.*)$') { $e += "seg ${n}: unknown header '$h'"; continue }
    $t = $Matches[1]; $f = @($Matches[2] -split '\|' | ForEach-Object { $_.Trim() }); $a = @($f[0] -split '\s+')
    if ($t -eq 'photo') { $photos++; $run = 0; if ($ai -notcontains $a[0] -and -not (Test-Path "$AE\photos\$($a[0])")) { $e += "seg ${n}: photo $($a[0]) has no '#ai $($a[0]) | prompt' line" }; continue }
    if ($t -eq 'char') { $run++; if ($run -eq 4) { $e += "seg ${n}: more than 3 char scenes in a row" } } else { $run = 0 }
    $sp, $bg = $a[0], $a[1]
    if (-not $m.sp.ContainsKey("$sp")) { $e += "seg ${n}: sprite '$sp' not approved" } elseif (-not $m.bg.ContainsKey("$bg")) { $e += "seg ${n}: background '$bg' not approved" } elseif ($m.bg[$bg] -notcontains $m.sp[$sp]) { $e += "seg ${n}: $sp ($($m.sp[$sp])) not allowed on $bg [$($m.bg[$bg] -join ',')]" }
    if ($need[$t] -and ($f.Count - 1) -lt $need[$t]) { $e += "seg ${n}: @$t needs $($need[$t]) fields after the sprite/background" }
    if ($t -eq 'bars') { foreach ($x in ($f[3] -split ';;')) { if ($x -notmatch ':\s*-?\d+(\.\d+)?\s*$') { $e += "seg ${n}: bars item '$x' needs label:number" } } }
    if ($t -eq 'curve' -and $f[4] -notmatch '^-?\d+(\.\d+)?$') { $e += "seg ${n}: curve peak must be a number" }
  }
  if ($n -lt 15) { $e += "only $n segments (need 25-45)" }
  if ($words -lt 1200) { $e += "only $words words (need 1,500-1,800)" }
  if ($photos -lt 1) { $e += 'no @photo scene' }
  @{ errors = $e; words = $words; segs = $n }
}
function CheckThumb($th) {
  $m = Manifest; $e = @()
  if ("$($th.text)" -notmatch '^[^|]+\|[^|]+$') { $e += 'thumb.text must be LINE1|LINE2' } elseif ((("$($th.text)" -replace '\|', ' ') -split '\s+' | Where-Object { $_ }).Count -gt 3) { $e += 'thumb.text max 3 words' }
  if (-not $m.sp.ContainsKey("$($th.sprite)")) { $e += "thumb sprite '$($th.sprite)' not approved" } elseif (-not $m.bg.ContainsKey("$($th.bg)")) { $e += "thumb bg '$($th.bg)' not approved" } elseif ($m.bg[$th.bg] -notcontains $m.sp[$th.sprite]) { $e += "thumb $($th.sprite) not allowed on $($th.bg)" }
  if ($th.accent -and "$($th.accent)" -notmatch '^#[0-9A-Fa-f]{6}$') { $e += 'accent must be #RRGGBB' }
  $e
}

# ---------- pipeline (one Crazy Facts video) ----------
function Plan($id) { RJ "$AE\videos\$id.json" }
function BlockFile($b) { "$F\scripts\$b.txt" }
function Position($n, $total) { if ($n -eq 1) { 'This is block 1: open with the 15-second gentle hook and the "Tonight, we''ll explore" list (no numbers).' } elseif ($n -eq $total) { 'This is the LAST block: practical takeaways, a callback to the opening moment, a gentle guided wind-down, then an @end segment teasing the next video.' } else { 'Middle block: continue the story with a spoken transition; no greeting, no recap, no ending.' } }
function Advance($id) {
  $p = RJ "$S\pipelines\$id.json"; if (-not $p -or $p.stage -in 'render_requested', 'rendered', 'blocked') { return }
  $plan = Ensure 'cf_plan' $id @{ id = $id } @() $id
  if (-not (Done $plan)) { return }
  $v = Plan $id; $parts = @($v.parts); $settled = 0
  $thumb = Ensure 'cf_thumb' $id @{ id = $id } @($plan) $id
  foreach ($b in $parts) {
    $bt = Ensure 'cf_block' $b @{ id = $id; block = $b } @($plan) $id
    if (Done $bt) {
      $au = Ensure 'cf_audit' $b @{ id = $id; block = $b } @($bt) $id
      if (Done $au) { $r = RJ "$S\out\cf_audit-$b.json"; $fx = "cf_fix-$b"; if (-not $r.needs_fix -or (Done $fx) -or (Test-Path "$S\queue\failed\$fx.json")) { $settled++ } }
    }
    if (Test-Path "$S\queue\failed\cf_block-$b.json") { $p.stage = 'blocked'; $p.why = "block $b failed"; WJ "$S\pipelines\$id.json" $p; Notify 'Factory: pipeline blocked' "$id - $b failed $((Cfg).max_attempts)x"; return }
  }
  $p.blocks = "$settled/$($parts.Count)"
  if ($settled -eq $parts.Count) {
    $sh = Ensure 'cf_shorts' $id @{ id = $id } @() $id
    if ((Done $sh) -and (Done $thumb)) { $p.stage = 'ready_to_render' } else { $p.stage = 'shorts' }
  } else { $p.stage = 'writing' }
  WJ "$S\pipelines\$id.json" $p
}

# ---------- prompts per task type (built fresh at claim time) ----------
function Fill($tpl, $vars) { $t = Get-Content "$F\prompts\$tpl.md" -Raw -Encoding utf8; foreach ($k in $vars.Keys) { $t = $t.Replace("{{$k}}", "$($vars[$k])") }; $t }
function Digest($v) {
  $out = @()
  foreach ($b in $v.parts) {
    $tx = Get-Content (BlockFile $b) -Raw -Encoding utf8; $i = 0; $sec = 0.0
    foreach ($L in (Segs ($tx -split "`nSOURCES:")[0])) {
      if ($L[0].StartsWith('#')) { continue }
      $say = ($L | Select-Object -Skip 1) -join ' '; $w = ($say -split '\s+').Count; $sn = ([regex]::Matches($say, '[.!?](\s|$)')).Count
      $type = ($L[0] -split '\s')[0].TrimStart('@')
      $out += "[$b #$i ~$('{0:00}:{1:00}' -f [math]::Floor($sec / 60), [int]($sec % 60)) | $type | ${w}w] $say"
      $sec += $w * 60 / 183 + $sn * 0.85 + 0.5; $i++
    }
  }
  $out -join "`n"
}
function Prompt($t) {
  $a = $t.args; $v = if ($a.id) { Plan $a.id }
  switch ($t.type) {
    'cf_plan' { Fill 'cf_plan' @{ id = $a.id } }
    'cf_block' {
      $parts = @($v.parts); $n = [array]::IndexOf($parts, $a.block) + 1; $plan = @($v.plan)
      $fam = if ($v.thumb.sprite -match '^([A-Z]+)') { $Matches[1] } else { 'A' }
      Fill 'cf_block' @{ n = $n; total = $parts.Count; block = $a.block; title = $v.title; format = $v.format; plan = ($plan -join "`n"); outline = $plan[$n - 1]; prev = $(if ($n -gt 1) { $plan[$n - 2] } else { '(this is the opening)' }); next = $(if ($n -lt $parts.Count) { $plan[$n] } else { '(this is the end)' }); family = $fam; position = (Position $n $parts.Count) }
    }
    'cf_fix' { $r = RJ "$S\out\$($a.from).json"; Fill 'cf_fix' @{ block = $a.block; title = $v.title; issues = ((@($r.issues) | ForEach-Object { "- $_" }) -join "`n"); text = (Get-Content (BlockFile $a.block) -Raw -Encoding utf8) } }
    'cf_audit' { $parts = @($v.parts); $n = [array]::IndexOf($parts, $a.block) + 1; Fill 'cf_audit' @{ block = $a.block; title = $v.title; position = (Position $n $parts.Count); outline = @($v.plan)[$n - 1]; text = (Get-Content (BlockFile $a.block) -Raw -Encoding utf8) } }
    'cf_shorts' { Fill 'cf_shorts' @{ id = $a.id; title = $v.title; count = [math]::Min(@($v.parts).Count, 12); digest = (Digest $v) } }
    'cf_thumb' { Fill 'cf_thumb' @{ id = $a.id; title = $v.title; plan = (@($v.plan) -join ' / '); thumb = ($v.thumb | ConvertTo-Json -Compress) } }
    'cf_analyze' {
      $st = RJ "$Repo\studio\yt\status.json"; $rows = @()
      foreach ($x in @($st.videos)) { $rows += "- $($x.published) | $($x.duration) | views $($x.views) likes $($x.likes) comments $($x.comments) | $($x.title)" }
      foreach ($x in (VideoMeta | Select-Object -Last 8)) { $rows += "- made: $($x.id) `"$($x.title)`" format $($x.format) thumb `"$($x.thumb.text)`" $($x.thumb.sprite)/$($x.thumb.bg)/$($x.thumb.accent)" }
      $pr = if (Test-Path "$S\proposals.md") { Get-Content "$S\proposals.md" -Raw -Encoding utf8 } else { 'none' }
      Fill 'cf_analyze' @{ videos = ($rows -join "`n"); proposals = $pr }
    }
  }
}

# ---------- deliverable handling ----------
function Deliverable($raw, $hash) {
  $lines = @(($raw -replace "`r", '') -split "`n" | Where-Object { $_ -notmatch '^\s*```' })
  $i = 0; while ($i -lt $lines.Count -and $lines[$i] -notmatch '^\s*STYLE\s+\w+') { $i++ }
  if ($i -ge $lines.Count) { return @{ err = 'first line must be "STYLE <version>" (agent did not sync with the context pack)' } }
  if ($lines[$i] -notmatch "STYLE\s+$hash") { return @{ err = "deliverable synced to an old style version: $($lines[$i])" } }
  $body = @(); $extra = @()
  foreach ($l in ($lines | Select-Object -Skip ($i + 1))) { if ($l -match '^\s*(PROPOSAL|REQUEST):') { $extra += $l.Trim() } else { $body += $l } }
  @{ body = ($body -join "`n").Trim(); extra = $extra }
}
function JsonOf($s) { $a = $s.IndexOfAny([char[]]'{['); if ($a -lt 0) { throw 'no JSON found' }; $s.Substring($a) | ConvertFrom-Json -AsHashtable }
function Accept($t, $body) {
  $a = $t.args
  switch ($t.type) {
    'cf_plan' {
      $v = JsonOf $body; $e = @()
      foreach ($k in 'title', 'desc', 'tags', 'format', 'thumb', 'parts', 'plan') { if (-not $v.$k) { $e += "missing $k" } }
      if (@($v.parts).Count -ne @($v.plan).Count) { $e += 'parts and plan must have the same length' }
      if (@($v.parts).Count -lt 3 -or @($v.parts).Count -gt 16) { $e += 'between 3 and 16 blocks' }
      $v.id = $a.id; $v.parts = @(1..@($v.parts).Count | ForEach-Object { '{0}_b{1:00}' -f $a.id, $_ }); $v.vibe = 'calm'; $v.voice = 'am_michael'; if (-not $v.sources) { $v.sources = @() }
      $e += CheckThumb $v.thumb; if ($e) { return $e }
      Lock { WJ "$AE\videos\$($a.id).json" $v; $s = @(RJ "$AE\videos\series.json"); if (-not ($s | Where-Object { $_.id -eq $a.id })) { $s += [ordered]@{ id = $a.id; title = $v.title }; WJ "$AE\videos\series.json" $s } }
    }
    { $_ -in 'cf_block', 'cf_fix' } {
      $parts = $body -split "`n\s*SOURCES:\s*`n?", 2; $txt = $parts[0].Trim(); $src = @(); if ($parts.Count -gt 1) { $src = @($parts[1] -split "`n" | ForEach-Object { $_.Trim(' -*') } | Where-Object { $_.Length -gt 10 }) }
      $c = CheckBlock $txt $a.block; if ($c.errors) { return $c.errors }
      if (-not $src) { return @('no SOURCES list') }
      Lock { WT (BlockFile $a.block) ($txt + "`n"); $v = Plan $a.id; $v.sources = @(@($v.sources) + $src | Select-Object -Unique); WJ "$AE\videos\$($a.id).json" $v }
      $script:outWords = $c.words
    }
    'cf_audit' {
      $r = JsonOf $body; $pass = (Cfg).audit_pass_score
      $r.needs_fix = [bool]($r.fix -and [int]$r.score -lt $pass -and @($r.issues).Count -gt 0); WJ "$S\out\$($t.id).json" $r
      if ($r.needs_fix) { Ensure 'cf_fix' $a.block @{ id = $a.id; block = $a.block; from = $t.id } @() $a.id | Out-Null }
    }
    'cf_shorts' {
      $arr = @(JsonOf $body); $v = Plan $a.id; $e = @(); $nn = $a.id.Substring(2)
      $keep = @(); $seen = @{}
      foreach ($x in $arr) {
        if ($v.parts -notcontains $x.src) { $e += "unknown src $($x.src)"; continue }
        if ($seen[$x.src]) { continue }; $seen[$x.src] = 1
        $segs = @(Segs ((Get-Content (BlockFile $x.src) -Raw -Encoding utf8)) | Where-Object { -not $_[0].StartsWith('#') })
        if ([int]$x.first -lt 0 -or [int]$x.last -lt [int]$x.first -or [int]$x.last -ge $segs.Count) { $e += "$($x.src): bad range $($x.first)-$($x.last)"; continue }
        $w = 0; for ($i = [int]$x.first; $i -le [int]$x.last; $i++) { $w += (($segs[$i] | Select-Object -Skip 1) -join ' ' -split '\s+').Count }
        if ($w -lt 55 -or $w -gt 175) { $e += "$($x.src) $($x.first)-$($x.last): $w words (needs ~65-150)"; continue }
        if ("$($x.top)".TrimEnd().EndsWith(':')) { $x.top = "$($x.top)".TrimEnd(':', ' ') + '.' }
        $keep += [ordered]@{ id = 'sh{0}_{1}' -f $nn, $x.src.Substring($x.src.Length - 2); src = $x.src; first = [int]$x.first; last = [int]$x.last; top = $x.top; title = $x.title; tags = @($x.tags) }
      }
      if ($keep.Count -lt [math]::Min(3, @($v.parts).Count)) { return @("only $($keep.Count) valid Shorts") + $e }
      WJ "$S\out\$($t.id).json" $arr
      Lock { $all = @(RJ "$AE\videos\shorts.json" | Where-Object { $_.src -notlike "$($a.id)_*" }); WJ "$AE\videos\shorts.json" @($all + $keep) }
      $script:outShorts = $keep.Count
    }
    'cf_thumb' {
      $th = JsonOf $body; $e = CheckThumb $th; if ($e) { return $e }
      $why = $th.why; $th.Remove('why'); Lock { $v = Plan $a.id; $v.thumb = $th; WJ "$AE\videos\$($a.id).json" $v }
    }
    'cf_analyze' {
      $ins = if ($body -match '(?s)INSIGHTS:\s*(.*?)\s*RULES:') { $Matches[1].Trim() } else { return @('missing INSIGHTS:/RULES: sections') }
      $rules = ($body -split 'RULES:', 2)[1].Trim()
      Lock {
        [IO.File]::AppendAllText("$Repo\studio\insights.md", "`n## $(Today) (factory analyst)`n$ins`n", $Utf8)
        if ($rules -and $rules -notmatch '^none') { $l = Get-Content "$F\learned.md" -Raw -Encoding utf8; WT "$F\learned.md" ($l.TrimEnd() + "`n" + $rules + "`n") }
        if (Test-Path "$S\proposals.md") { Move-Item "$S\proposals.md" "$S\proposals-$(Get-Date -f yyyyMMddHHmm).md" -Force }
      }
    }
  }
  @()
}

# ---------- run one agent headless ----------
function Run($ag, $t, $prompt) {
  $c = Cfg; $tc = $c.types[$t.type]; $base = "$S\runs\$($t.id)-$($ag.name)-$(Get-Date -f HHmmss)"
  WT "$base.prompt.md" $prompt
  $kind = $ag.kind; $model = if ($kind -eq 'claude' -and $tc.claude_model) { $tc.claude_model } else { $ag.model }
  switch ($kind) {
    'codex' { $exe = $Exe.codex; $al = @('exec', '--json', '--skip-git-repo-check', '--ephemeral', '-s', 'read-only', '-C', "`"$Repo`"", '-c', 'web_search="live"', '-o', "`"$base.last.txt`"", '-') }
    'claude' { $exe = $Exe.claude; $al = @('-p', '--output-format', 'stream-json', '--verbose', '--allowedTools', 'Read', 'Glob', 'Grep', 'WebSearch', 'WebFetch'); if ($model) { $al += @('--model', $model) } }
    'copilot' { $exe = $Exe.copilot; $al = @('-s', '--no-color') }
  }
  $p = Start-Process -FilePath $exe -ArgumentList $al -WorkingDirectory $Repo -RedirectStandardInput "$base.prompt.md" -RedirectStandardOutput "$base.log" -RedirectStandardError "$base.err" -NoNewWindow -PassThru
  $t0 = Now; $lastSize = 0; $lastGrow = Now; $why = $null
  while (-not $p.HasExited) {
    Start-Sleep 5
    $sz = (Get-Item "$base.log").Length; if ($sz -ne $lastSize) { $lastSize = $sz; $lastGrow = Now }
    $el = (Now) - $t0
    $a = AState $ag.name; $a.state = 'working'; $a.elapsed = $el; SaveA $a
    Write-Host ("`r  {0} {1}  {2} elapsed, output {3}   " -f $ag.name, $t.id, (Fmt $el), (Num $sz)) -NoNewline
    if ($el -gt $tc.timeout_s) { $why = "timeout after $(Fmt $el)" }
    elseif (((Now) - $lastGrow) -gt $tc.stall_s -and $kind -ne 'copilot') { $why = "stalled: no output for $(Fmt ((Now) - $lastGrow))" }
    elseif (Test-Path "$S\kill\$($t.id)") { $why = 'taken over (kill flag)'; Remove-Item "$S\kill\$($t.id)" }
    if ($why) { & taskkill /PID $p.Id /T /F 2>$null | Out-Null; break }
  }
  Write-Host ''
  $log = Get-Content "$base.log" -Raw -Encoding utf8 -ErrorAction SilentlyContinue; $err = Get-Content "$base.err" -Raw -Encoding utf8 -ErrorAction SilentlyContinue
  $r = @{ ok = $false; text = ''; tin = 0; tout = 0; cached = 0; cost = 0.0; why = $why; secs = (Now) - $t0; rate = $false }
  # only real error events count as a rate limit (Claude logs an informational rate_limit_event on every run)
  $errEv = @("$log" -split "`n" | Where-Object { $_ -match '"type":"(error|turn\.failed)"|"is_error":true' -and $_ -notmatch 'hook timeout' }) -join ' '
  if ("$err $errEv" -match '(?i)rate.?limit|usage limit|quota exceeded|too many requests|\b429\b|hit your (usage )?limit|credit balance' -or "$log" -match '"rate_limit_event".{0,80}"status":"(rejected|blocked)"') { $r.rate = $true }
  switch ($kind) {
    'codex' {
      foreach ($l in ($log -split "`n")) { if ($l -match '"turn.completed"') { $u = ($l | ConvertFrom-Json -AsHashtable).usage; $r.tin += $u.input_tokens - $u.cached_input_tokens; $r.cached += $u.cached_input_tokens; $r.tout += $u.output_tokens + $u.reasoning_output_tokens } }
      if (Test-Path "$base.last.txt") { $r.text = Get-Content "$base.last.txt" -Raw -Encoding utf8 }
    }
    'claude' {
      $res = $null; foreach ($l in ($log -split "`n")) { if ($l -match '"type":"result"' -and $l -match '"usage"') { try { $j = $l | ConvertFrom-Json -AsHashtable; if ($j.type -eq 'result') { $res = $j } } catch {} } }
      if ($res) { $u = $res.usage; $r.text = "$($res.result)"; $r.tin = $u.input_tokens + $u.cache_creation_input_tokens; $r.cached = $u.cache_read_input_tokens; $r.tout = $u.output_tokens; $r.cost = [double]$res.total_cost_usd; if ($res.is_error) { $r.why = "claude error: $($res.result)" } }
    }
    'copilot' { $r.text = $log; $r.tin = [int]($prompt.Length / 4); $r.tout = [int]("$log".Length / 4) }
  }
  if (-not $r.why -and -not "$($r.text)".Trim()) { $m = ("$err $log".Trim() -replace '\s+', ' '); $r.why = 'empty answer: ' + $m.Substring([math]::Max(0, $m.Length - 200)) }
  $r.ok = -not $r.why; $r
}

# ---------- worker ----------
function MayTake($ag, $t, $c, $agents) {
  $tc = $c.types[$t.type]; if (-not $tc) { return $false }
  if ($t.avoid -contains $ag.name) { $others = $agents | Where-Object { $_.enabled -and $_.name -ne $ag.name -and ($tc.prefer + $tc.fallback) -contains $_.kind -and $t.avoid -notcontains $_.name }; if ($others) { return $false } }
  foreach ($d in $t.deps) { if (-not (Done $d)) { return $false } }
  if ($tc.prefer -contains $ag.kind) { return $true }
  if ($tc.fallback -notcontains $ag.kind) { return $false }
  $waited = (Now) - $t.queued; $livePref = $agents | Where-Object { $_.enabled -and $tc.prefer -contains $_.kind -and (Alive $_.name) }
  ($waited -gt $tc.spill_after_s) -or -not $livePref
}
function Worker($n) {
  $pane = $env:HERDR_PANE_ID
  if ($pane) { Herdr pane rename $pane "$n" | Out-Null }
  Write-Host "worker $n started (pane $pane). Ctrl+C stops it; its task is re-queued by the controller."
  $lastState = ''
  while ($true) {
    $c = Cfg; $agents = Agents; $ag = $agents | Where-Object { $_.name -eq $n }
    if (-not $ag) { Write-Host "agent $n is not in agents.json"; Start-Sleep 30; continue }
    $a = AState $n; $a.kind = $ag.kind; $a.pane = $pane; $a.pid = $PID
    $ctl = Ctl; $state = 'idle'
    if (-not $ag.enabled) { $state = 'disabled' } elseif ($ctl.paused) { $state = 'paused' } elseif ($a.cooldown_until -gt (Now)) { $state = 'cooldown' } elseif (($a.tin + $a.tout) -gt $ag.daily_token_cap) { $state = 'capped' }
    $a.state = $state; $a.task = $null; SaveA $a
    if ($pane -and $state -ne $lastState) { Herdr pane report-agent $pane --source factory --agent $ag.kind --state $(if ($state -eq 'idle') { 'idle' } else { 'unknown' }) --message "$n $state" | Out-Null; $lastState = $state }
    if ($state -ne 'idle') { Start-Sleep 20; continue }
    $claimed = $null
    foreach ($t in (Tasks 'pending' | Sort-Object { $_.priority }, { $_.queued })) {
      if (-not (MayTake $ag $t $c $agents)) { continue }
      try { [IO.File]::Move("$S\queue\pending\$($t.id).json", "$S\queue\active\$($t.id).json"); $claimed = $t; break } catch { }
    }
    if (-not $claimed) { Start-Sleep 10; continue }
    $t = $claimed; $t.agent = $n; $t.started = Now; WJ "$S\queue\active\$($t.id).json" $t
    $a.task = $t.id; $a.state = 'working'; $a.since = Now; SaveA $a
    Write-Host "$(Get-Date -f HH:mm:ss) $n took $($t.id) (attempt $($t.attempts + 1))"
    if ($pane) { Herdr pane report-agent $pane --source factory --agent $ag.kind --state working --message "$n · $($t.id)" | Out-Null; $lastState = 'working' }
    Ev @{ ev = 'start'; task = $t.id; type = $t.type; agent = $n; kind = $ag.kind }
    $pk = Pack; $script:outWords = 0; $script:outShorts = 0
    try { $body = Prompt $t } catch { $body = $null; $perr = "$_" }
    if (-not $body) { Requeue $t "$S\queue\active\$($t.id).json" $n "prompt build failed: $perr"; continue }
    if ($t.last_errors) { $body += "`n`nA previous attempt (another agent) was rejected. Avoid exactly these problems:`n" + ((@($t.last_errors) | ForEach-Object { "- $_" }) -join "`n") }
    $prompt = "$($pk.text)`n`n---`n$body`n`n---`nOUTPUT CONTRACT: reply with ONLY the deliverable. The very first line must be exactly: STYLE $($pk.hash)`nThen the deliverable in the format above. Optional after it: lines starting with PROPOSAL: or REQUEST: (STYLE section 10). No code fences, no commentary. Do not edit any files."
    try { $r = Run $ag $t $prompt } catch { $r = @{ ok = $false; why = "worker error: $_"; tin = 0; tout = 0; cached = 0; cost = 0.0; secs = 0; rate = $false } }
    $a = AState $n; $a.tin += $r.tin; $a.tout += $r.tout; $a.cached += $r.cached; $a.cost += $r.cost; $a.busy += $r.secs
    $errs = @()
    if ($r.ok) {
      $d = Deliverable $r.text $pk.hash
      if ($d.err) { $errs = @($d.err) } else {
        try { $errs = @(Accept $t $d.body) } catch { $errs = @("could not use the deliverable: $_") }
        foreach ($x in $d.extra) {
          if ($x -match '^PROPOSAL:\s*(.+)') { [IO.File]::AppendAllText("$S\proposals.md", "- $(Today) $n ($($t.id)): $($Matches[1])`n", $Utf8) }
          if ($x -match '^REQUEST:\s*(\{.+\})') { WT "$S\inbox\$n-$(Get-Date -f yyyyMMddHHmmssfff).json" $Matches[1] }
        }
      }
    } else { $errs = @($r.why) }
    $ev = @{ ev = 'end'; task = $t.id; type = $t.type; agent = $n; kind = $ag.kind; secs = $r.secs; tin = $r.tin; tout = $r.tout; cached = $r.cached; cost = $r.cost; words = $script:outWords; shorts = $script:outShorts }
    if (-not $errs) {
      $t.finished = Now; $t.secs = $r.secs; WJ "$S\queue\done\$($t.id).json" $t; Remove-Item "$S\queue\active\$($t.id).json" -ErrorAction SilentlyContinue
      $a.done++; $a.fails = 0; $ev.ok = $true; Ev $ev; Write-Host "$(Get-Date -f HH:mm:ss) $n DONE $($t.id) in $(Fmt $r.secs), tokens in $(Num $r.tin) out $(Num $r.tout)" -ForegroundColor Green
      if ($t.pipeline) { Lock { Advance $t.pipeline } }
    } else {
      $a.failed++; $a.fails++; $ev.ok = $false; $ev.why = ($errs | Select-Object -First 3) -join '; '; Ev $ev
      Write-Host "$(Get-Date -f HH:mm:ss) $n FAILED $($t.id): $($ev.why)" -ForegroundColor Red
      if ($r.rate) { $a.cooldown_until = (Now) + $c.ratelimit_cooldown_s; Ev @{ ev = 'cooldown'; agent = $n; why = 'rate limit' } }
      elseif ($a.fails -ge $c.cooldown_after_failures) { $a.cooldown_until = (Now) + $c.cooldown_s; $a.fails = 0; Ev @{ ev = 'cooldown'; agent = $n; why = "$($c.cooldown_after_failures) failures in a row" } }
      # failed validation of a block: the next attempt gets the errors as a fix list
      $t.last_errors = @($errs | Select-Object -First 12)
      Requeue $t "$S\queue\active\$($t.id).json" $n (($errs | Select-Object -First 2) -join '; ')
    }
    SaveA $a
  }
}

# ---------- controller ----------
function Inventory {
  $now = [DateTimeOffset]::Now; $n = 0; $items = @()
  foreach ($d in (Get-ChildItem "$Repo\studio\renders" -Directory -Filter 'lf*')) {
    $r = RJ "$($d.FullName)\result.json"; if (-not $r) { continue }
    $when = if ($r.scheduled) { [DateTimeOffset]::Parse($r.scheduled) }
    if (-not $when) { $n++; $items += "$($d.Name) rendered, not scheduled" } elseif ($when -gt $now) { $n++; $items += "$($d.Name) airs $($when.ToString('MM-dd HH:mm'))" }
  }
  foreach ($p in (Get-ChildItem "$S\pipelines" -Filter *.json)) { $pp = RJ $p.FullName; if ($pp.stage -ne 'rendered' -and -not (Test-Path "$Repo\studio\renders\$($pp.id)\result.json")) { $n++; $items += "$($pp.id) $($pp.stage)" } }
  @{ count = $n; items = $items }
}
function NextId { $m = 0; foreach ($vf in (Get-ChildItem "$AE\videos" -Filter 'lf??.json')) { $m = [math]::Max($m, [int]$vf.BaseName.Substring(2)) }; foreach ($vf in (Get-ChildItem "$S\pipelines" -Filter 'lf*.json')) { $m = [math]::Max($m, [int]$vf.BaseName.Substring(2)) }; 'lf{0:00}' -f ($m + 1) }
function StartVideo { $id = NextId; WJ "$S\pipelines\$id.json" ([ordered]@{ id = $id; channel = 'crazyfacts'; created = Now; stage = 'planning' }); Ev @{ ev = 'pipeline'; id = $id }; Lock { Advance $id }; $id }
function GitPush($paths, $msg) {
  Push-Location $Repo
  try {
    & $Git add -- @paths 2>$null; & $Git commit -q -m $msg 2>$null | Out-Null
    & $Git pull -q --rebase --autostash 2>$null; & $Git push -q 2>$null; $LASTEXITCODE -eq 0
  } finally { Pop-Location }
}
function Controller {
  Write-Host 'controller started: planner, watchdog, failover, git hand-off'
  if ($env:HERDR_PANE_ID) { Herdr pane rename $env:HERDR_PANE_ID 'controller' | Out-Null }
  while ($true) {
    try { Tick } catch { Write-Host "$(Get-Date -f HH:mm:ss) tick error: $_" -ForegroundColor Red; Ev @{ ev = 'error'; where = 'controller'; why = "$_" } }
    Start-Sleep (Cfg).tick_s
  }
}
function Tick {
  $c = Cfg; $ctl = Ctl; $agents = Agents; $now = Now
  WT "$S\controller.hb" "$now"
  # 1. stay in sync with GitHub (render results, stats)
  if ($now - $ctl.last_pull -gt $c.git_pull_every_s) { Push-Location $Repo; & $Git pull -q --rebase --autostash 2>$null; Pop-Location; $ctl.last_pull = $now }
  # 2. watchdog: dead workers and over-time tasks -> another agent takes over
  foreach ($t in (Tasks 'active')) {
    $a = RJ "$S\agents\$($t.agent).json"
    if (-not $t.started -or ($now - $t.started) -lt 60) { continue }  # just claimed: give the worker a moment to write its heartbeat
    if (-not $a -or ($now - $a.hb) -gt $c.heartbeat_stale_s -or $a.task -ne $t.id) { Write-Host "$(Get-Date -f HH:mm:ss) failover: $($t.id) (worker $($t.agent) silent)" -ForegroundColor Yellow; Requeue $t "$S\queue\active\$($t.id).json" $t.agent 'worker went silent (failover)'; continue }
    if (($now - $t.started) -gt ($c.types[$t.type].timeout_s + 120)) { WT "$S\kill\$($t.id)" 'x' }
  }
  # 3. requests agents sent to each other
  $recent = @(Get-Content "$S\events.jsonl" -Tail 400 -ErrorAction SilentlyContinue | ForEach-Object { $_ | ConvertFrom-Json -AsHashtable } | Where-Object { $_.ev -eq 'inbox' -and $now - $_.ts -lt 3600 }).Count
  foreach ($ib in (Get-ChildItem "$S\inbox" -Filter *.json)) {
    try { $r = Get-Content $ib.FullName -Raw | ConvertFrom-Json -AsHashtable } catch { $r = $null }
    if ($r -and $c.inbox_types -contains $r.type -and $recent -lt $c.inbox_max_per_hour -and $r.args.id) {
      $key = if ($r.args.block) { $r.args.block } else { "$($r.args.id)-$(Get-Date -f MMddHHmm)" }; Ensure $r.type $key $r.args @() $r.args.id | Out-Null; $recent++
      Ev @{ ev = 'inbox'; type = $r.type; by = $ib.BaseName; reason = $r.reason }
    }
    Remove-Item $ib.FullName
  }
  # 4. advance pipelines; hand finished ones to GitHub Actions for rendering
  foreach ($pf in (Get-ChildItem "$S\pipelines" -Filter *.json)) {
    $id = $pf.BaseName; Lock { Advance $id }; $p = RJ $pf.FullName
    if ($p.stage -eq 'render_requested' -and (Test-Path "$Repo\studio\renders\$id\result.json")) { $p.stage = 'rendered'; WJ $pf.FullName $p; Ev @{ ev = 'rendered'; id = $id }; Notify 'Factory: video rendered' "$id is rendered; channel-operator QCs and schedules it" }
    if ($p.stage -eq 'ready_to_render' -and $c.channels.crazyfacts.push_render) {
      $v = Plan $id; WJ "$F\render\$id.json" ([ordered]@{ id = $id; title = $v.title; parts = $v.parts; requested = (Get-Date).ToString('s') })
      $paths = @("studio/factory/scripts", "studio/factory/render/$id.json", "studio/assetedit/videos/$id.json", 'studio/assetedit/videos/shorts.json', 'studio/assetedit/videos/series.json', 'studio/factory/learned.md', 'studio/insights.md')
      if (GitPush $paths "factory: $id `"$($v.title)`" written (Codex/Claude), render requested") { $p.stage = 'render_requested'; $p.pushed = $now; WJ $pf.FullName $p; Ev @{ ev = 'render'; id = $id }; Notify 'Factory: render requested' "$id `"$($v.title)`" pushed to GitHub Actions" }
      else { Write-Host 'git push failed; retry next tick' -ForegroundColor Yellow }
    }
  }
  # 5. watermarks: generate only when the buffer runs low, stop when it is full
  $cf = $c.channels.crazyfacts
  if ($cf.enabled -and -not $ctl.paused) {
    $inv = Inventory
    if ($inv.count -lt $cf.low_watermark) { $ctl.cf_mode = 'generating' } elseif ($inv.count -ge $cf.high_watermark) { $ctl.cf_mode = 'paused' }
    $open = @(Get-ChildItem "$S\pipelines" -Filter *.json | ForEach-Object { RJ $_.FullName } | Where-Object { $_.stage -notin 'render_requested', 'rendered', 'blocked' }).Count
    $startedToday = [int]$ctl.started[(Today)]
    if ($ctl.cf_mode -eq 'generating' -and $open -lt $cf.max_concurrent_pipelines -and $startedToday -lt $cf.max_pipelines_started_per_day) {
      $id = StartVideo; $ctl.started[(Today)] = $startedToday + 1; Write-Host "$(Get-Date -f HH:mm:ss) buffer $($inv.count) (refill to $($cf.high_watermark)): started $id" -ForegroundColor Cyan
    }
    $ctl.cf_buffer = $inv.count; $ctl.cf_items = $inv.items
  }
  # 6. recurring analysis, only when there is new data
  $ra = $c.recurring.cf_analyze; $sf = "$Repo\$($ra.only_if_changed)"
  if ($ra -and (Test-Path $sf) -and $now - $ctl.last_analyze -gt $ra.every_s) {
    $h = (Get-FileHash $sf -Algorithm SHA1).Hash
    if ($h -ne $ctl.analyze_hash) { Ensure 'cf_analyze' (Get-Date -f yyyyMMdd) @{} @() $null | Out-Null; $ctl.analyze_hash = $h }
    $ctl.last_analyze = $now
  }
  # 7. tell Herdr
  $pend = @(Tasks 'pending').Count; $act = @(Tasks 'active').Count
  $ws = $env:HERDR_WORKSPACE_ID; if ($ws) { Herdr workspace report-metadata $ws --source factory --token "buffer=$($ctl.cf_buffer)" --token "mode=$($ctl.cf_mode)" --token "queue=$pend/$act" | Out-Null }
  SaveCtl $ctl
}

# ---------- dashboard ----------
function Render {
  $c = Cfg; $ctl = Ctl; $now = Now; $E = [char]27; $W = [math]::Max(100, $Host.UI.RawUI.WindowSize.Width)
  $G = "$E[32m"; $R = "$E[31m"; $Y = "$E[33m"; $B = "$E[36m"; $Dm = "$E[2m"; $Bo = "$E[1m"; $X = "$E[0m"
  $o = [Collections.Generic.List[string]]::new()
  $hbC = [int](Get-Content "$S\controller.hb" -ErrorAction SilentlyContinue); $cOk = ($now - $hbC) -lt 120
  $mode = if ($ctl.paused) { "${R}PAUSED (manual)$X" } elseif ($ctl.cf_mode -eq 'generating') { "${G}GENERATING$X" } else { "${Y}IDLE: buffer full$X" }
  $hash = Get-Content "$S\pack.hash" -ErrorAction SilentlyContinue
  $o.Add("$Bo CRAZY FACTS FACTORY$X  $(Get-Date -f 'ddd dd MMM HH:mm:ss')   controller $(if ($cOk) { "${G}live$X" } else { "${R}DOWN$X" })   mode $mode   style ${B}v$hash$X")
  $cf = $c.channels.crazyfacts; $bar = ('#' * [int]$ctl.cf_buffer).PadRight($cf.high_watermark, '.')
  $o.Add(" Buffer [$bar] $($ctl.cf_buffer) videos (resume < $($cf.low_watermark), stop at $($cf.high_watermark))  $Dm$(@($ctl.cf_items) -join ' · ')$X")
  $o.Add('')
  $o.Add("$Bo AGENTS$X")
  $o.Add(('{0,-10} {1,-8} {2,-10} {3,-26} {4,9} {5,6} {6,6} {7,7} {8,8} {9,8} {10,7}' -f 'name', 'kind', 'state', 'task', 'elapsed', 'done', 'fail', 'ok%', 'tok in', 'tok out', 'cost$'))
  $ev = @(Get-Content "$S\events.jsonl" -Tail 3000 -ErrorAction SilentlyContinue | ForEach-Object { $_ | ConvertFrom-Json -AsHashtable })
  $dayStart = [DateTimeOffset]::new((Get-Date).Date).ToUnixTimeSeconds(); $evToday = @($ev | Where-Object { $_.ts -ge $dayStart })
  $tot = @{ tin = 0; tout = 0; cost = 0.0 }
  foreach ($ag in (Agents)) {
    $a = RJ "$S\agents\$($ag.name).json"; $st = 'offline'; $col = $Dm
    if ($a -and $a.day -eq (Today)) { $tot.tin += $a.tin; $tot.tout += $a.tout; $tot.cost += $a.cost }
    if (-not $ag.enabled) { $st = 'disabled' } elseif ($a -and ($now - $a.hb) -lt $c.heartbeat_stale_s) { $st = $a.state; $col = @{ working = $G; idle = $B; cooldown = $Y; capped = $Y; paused = $Y }[$st] }
    $d = if ($a.day -eq (Today)) { [int]$a.done } else { 0 }; $fl = if ($a.day -eq (Today)) { [int]$a.failed } else { 0 }; $pct = if ($d + $fl) { [int](100 * $d / ($d + $fl)) } else { '-' }
    $task = if ($st -eq 'working') { $a.task } elseif ($st -eq 'cooldown') { 'until ' + [DateTimeOffset]::FromUnixTimeSeconds($a.cooldown_until).ToLocalTime().ToString('HH:mm') } else { '' }
    $el = if ($st -eq 'working') { Fmt $a.elapsed } else { '' }
    $o.Add(("{0,-10} {1,-8} $col{2,-10}$X {3,-26} {4,9} {5,6} {6,6} {7,7} {8,8} {9,8} {10,7:0.00}" -f $ag.name, $ag.kind, $st, "$task".Substring(0, [math]::Min(26, "$task".Length)), $el, $d, $fl, $pct, (Num ([int]$a.tin)), (Num ([int]$a.tout)), [double]$a.cost))
  }
  $o.Add("$Dm today: tokens in $(Num $tot.tin) / out $(Num $tot.tout) (cached input not counted), Claude cost `$$('{0:0.00}' -f $tot.cost) (subscription: informational)$X")
  $o.Add('')
  $pend = @(Tasks 'pending' | Sort-Object { $_.priority }, { $_.queued }); $act = @(Tasks 'active'); $fail = @(Tasks 'failed')
  $doneToday = @($evToday | Where-Object { $_.ev -eq 'end' -and $_.ok }).Count
  $o.Add("$Bo QUEUE$X  pending $($pend.Count) · active $($act.Count) · done today $doneToday · failed $($fail.Count)")
  foreach ($t in $act) { $lim = $c.types[$t.type].timeout_s; $el = $now - $t.started; $cl = if ($el -gt 0.8 * $lim) { $R } else { $G }; $o.Add(("  ${cl}RUN $X {0,-28} by {1,-9} {2} / {3}" -f $t.id, $t.agent, (Fmt $el), (Fmt $lim))) }
  foreach ($t in ($pend | Select-Object -First 8)) { $tc = $c.types[$t.type]; $wt = $now - $t.queued; $blocked = @($t.deps | Where-Object { -not (Done $_) }).Count; $who = if ($blocked) { "waits for $blocked dep" } else { ($tc.prefer -join '/') + $(if ($wt -gt $tc.spill_after_s) { " + $($tc.fallback -join '/') (failover open)" } else { '' }) }; $o.Add(("  ${Dm}WAIT$X {0,-28} {1,8}  try {2}  -> {3}" -f $t.id, (Fmt $wt), ($t.attempts + 1), $who)) }
  if ($pend.Count -gt 8) { $o.Add("  $Dm... $($pend.Count - 8) more$X") }
  foreach ($t in ($fail | Select-Object -Last 3)) { $o.Add(("  ${R}FAIL$X {0,-28} {1}" -f $t.id, (@($t.history)[-1]))) }
  $o.Add('')
  $o.Add("$Bo PIPELINES$X")
  foreach ($p in (Get-ChildItem "$S\pipelines" -Filter *.json | Sort-Object Name -Descending | Select-Object -First 5 | ForEach-Object { RJ $_.FullName })) { $v = Plan $p.id; $o.Add(("  {0}  {1,-16} blocks {2,-6} {3}" -f $p.id, $p.stage, $p.blocks, "$($v.title)")) }
  $o.Add('')
  $words = ($evToday | Where-Object { $_.ok } | Measure-Object -Property words -Sum).Sum; $shorts = ($evToday | Where-Object { $_.ok } | Measure-Object -Property shorts -Sum).Sum
  $o.Add("$Bo OUTPUT TODAY$X  script words $([int]$words) · Shorts cut $([int]$shorts) · renders requested $(@($evToday | Where-Object ev -eq 'render').Count) · failovers $(@($evToday | Where-Object ev -eq 'requeued').Count)")
  $byType = $ev | Where-Object { $_.ev -eq 'end' -and $_.ok } | Group-Object type | ForEach-Object { $s = $_.Group | Measure-Object -Property secs -Average; $tk = $_.Group | ForEach-Object { $_.tin + $_.tout } | Measure-Object -Average; "{0} {1}x avg {2} {3} tok" -f $_.Name, $_.Count, (Fmt $s.Average), (Num ([int]$tk.Average)) }
  if ($byType) { $o.Add("$Dm efficiency per task type: $($byType -join ' | ')$X") }
  $o.Add('')
  $o.Add("$Bo ALERTS / IMPROVEMENTS$X")
  $al = @()
  if (-not $cOk) { $al += "${R}controller is not running: no planning, no failover, no render hand-off$X" }
  foreach ($t in $act) { if (($now - $t.started) -gt 0.8 * $c.types[$t.type].timeout_s) { $al += "$($t.id) close to its timeout on $($t.agent): will be killed and moved to another agent" } }
  foreach ($t in $pend) { $tc = $c.types[$t.type]; $cap = @(Agents | Where-Object { $_.enabled -and ($tc.prefer + $tc.fallback) -contains $_.kind -and (Alive $_.name) }); if (-not $cap -and -not @($t.deps | Where-Object { -not (Done $_) })) { $al += "no live agent can do $($t.type) ($($t.id)): start a worker for $(($tc.prefer + $tc.fallback) -join '/')"; break } }
  foreach ($ag in (Agents | Where-Object enabled)) { $e2 = @($ev | Where-Object { $_.ev -eq 'end' -and $_.agent -eq $ag.name } | Select-Object -Last 10); $bad = @($e2 | Where-Object { -not $_.ok }).Count; if ($e2.Count -ge 4 -and $bad / $e2.Count -gt 0.4) { $al += "$($ag.name) fails $bad of its last $($e2.Count) tasks: check its pane / login" } }
  $vf = @($ev | Where-Object { $_.ev -eq 'end' -and -not $_.ok -and $_.why -match 'not allowed|not approved' }).Count; if ($vf -ge 3) { $al += "$vf failures on sprite/background pairs: the pack lists allowed pairs; consider a stricter example in STYLE section 4" }
  if (@($pend | Where-Object type -eq 'cf_block').Count -gt 2 * @(Agents | Where-Object { $_.enabled -and $_.kind -eq 'codex' }).Count) { $al += 'blocks are queuing: add a lane with  factory.ps1 add-agent -Name codex3 -Kind codex' }
  if ((Test-Path "$S\proposals.md")) { $al += "$(@(Get-Content "$S\proposals.md").Count) style proposals waiting for the analyst (next cf_analyze)" }
  if (-not $al) { $al += "${G}nothing stuck$X" }
  foreach ($x in ($al | Select-Object -First 8)) { $o.Add("  - $x") }
  $o.Add("$Dm keys: this pane only shows. Control: factory.ps1 pause|resume|new-video|add-agent|retry -Id|kill -Id   events: studio\factory\state\events.jsonl$X")
  [Console]::Write("$E[H$E[2J" + ($o -join "`n"))
}

switch ($Mode) {
  'controller' { Pack | Out-Null; Controller }
  'worker' { if (-not $Name) { throw '-Name required' }; Worker $Name }
  'dash' { if ($env:HERDR_PANE_ID) { Herdr pane rename $env:HERDR_PANE_ID 'dashboard' | Out-Null }; while ($true) { try { Render } catch { Write-Host "dash: $_" }; Start-Sleep 3 } }
  'status' { Render; Write-Host '' }
  'tick' { Tick; Write-Host 'tick done' }
  'pack' { $p = Pack; "pack v$($p.hash): $($p.text.Length) chars (~$([int]($p.text.Length / 4)) tokens) -> $S\pack.md" }
  'new-video' { $id = StartVideo; "started pipeline $id" }
  'enqueue' { $a = $Arg | ConvertFrom-Json -AsHashtable; $k = if ($a.block) { $a.block } elseif ($a.id) { $a.id } else { Get-Date -f MMddHHmmss }; Ensure $Type $k $a @() $a.id }
  'pause' { $c = Ctl; $c.paused = $true; SaveCtl $c; 'paused: workers finish their current task, then wait' }
  'resume' { $c = Ctl; $c.paused = $false; SaveCtl $c; 'resumed' }
  'retry' { $p = "$S\queue\failed\$Id.json"; $t = RJ $p; $t.attempts = 0; $t.avoid = @(); $t.queued = Now; WJ "$S\queue\pending\$Id.json" $t; Remove-Item $p; "re-queued $Id" }
  'kill' { WT "$S\kill\$Id" 'x'; "kill flag set for ${Id}: its worker stops it and the task fails over to another agent" }
  'add-agent' {
    if (-not $Name -or -not $Kind) { throw '-Name and -Kind required' }
    $l = [Collections.ArrayList]@(Agents); if ($l | Where-Object name -eq $Name) { throw "$Name exists" }
    $n = [ordered]@{ name = $Name; kind = $Kind; enabled = $true; daily_token_cap = 4000000; note = 'added ' + (Today) }; if ($Model) { $n.model = $Model }
    $l.Add($n) | Out-Null; WJ "$F\agents.json" @($l); "added $Name ($Kind)"
    & "$F\hq.ps1" -AddWorker $Name
  }
  default { Write-Host (Get-Content $PSCommandPath -TotalCount 14 | Select-Object -Skip 1) }
}
