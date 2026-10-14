<#
Builds the "CrazyFacts HQ" workspace in Herdr (idempotent):
  tab Control : dashboard (left) | controller (top right) + hq agent = Claude channel-operator you can talk to (bottom right)
  tab Workers : one pane per enabled agent in agents.json, each running "factory.ps1 worker -Name <agent>"
  hq.ps1                 create (or report) the workspace
  hq.ps1 -AddWorker x    add a worker pane for a new agent to the running workspace
  hq.ps1 -Focus          also switch the Herdr UI to it
#>
param([string]$AddWorker, [switch]$Focus, [switch]$NoHqAgent)
$ErrorActionPreference = 'Stop'
$F = $PSScriptRoot; $Repo = (Resolve-Path "$F\..\..").Path; $Label = 'CrazyFacts HQ'
$H = (Get-Command herdr -ErrorAction SilentlyContinue).Source; if (-not $H) { $H = "$env:USERPROFILE\.herdr\packages\standalone\current\herdr.exe" }
function Hd { param([Parameter(ValueFromRemainingArguments)]$a) $o = & $H @a; if ($LASTEXITCODE) { throw "herdr $($a -join ' ') failed" }; ($o -join "`n") | ConvertFrom-Json -AsHashtable }
function Cmd($mode, $name) { $n = if ($name) { " -Name $name" } else { '' }; "pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$F\factory.ps1`" $mode$n" }
function Run($pane, $cmd) { Hd pane run $pane $cmd | Out-Null }

$ws = (Hd workspace list).result.workspaces | Where-Object { $_.label -eq $Label } | Select-Object -First 1
if ($AddWorker) {
  if (-not $ws) { "HQ is not running; start it with hq.ps1 (the new agent is in agents.json and starts with it)"; return }
  $tab = (Hd tab list --workspace $ws.workspace_id).result.tabs | Where-Object { $_.label -eq 'Workers' } | Select-Object -First 1
  $last = (Hd pane list --workspace $ws.workspace_id).result.panes | Where-Object { $_.tab_id -eq $tab.tab_id } | Select-Object -Last 1
  $p = (Hd pane split $last.pane_id --direction down --cwd $Repo --no-focus).result.pane.pane_id
  Run $p (Cmd 'worker' $AddWorker); "worker $AddWorker started in pane $p"; return
}
if ($ws) { "$Label already exists ($($ws.workspace_id)). Open it in Herdr, or close it first to rebuild."; if ($Focus) { Hd workspace focus $ws.workspace_id | Out-Null }; return }

$r = (Hd workspace create --cwd $Repo --label $Label --no-focus).result
$wsId = $r.workspace.workspace_id; $ctlTab = $r.tab.tab_id; $dash = $r.root_pane.pane_id
Hd tab rename $ctlTab 'Control' | Out-Null
$ctl = (Hd pane split $dash --direction right --ratio 0.62 --cwd $Repo --no-focus).result.pane.pane_id
Run $dash (Cmd 'dash'); Run $ctl (Cmd 'controller')
if (-not $NoHqAgent) {
  $hq = (Hd pane split $ctl --direction down --ratio 0.35 --cwd $Repo --no-focus).result.pane.pane_id
  Start-Sleep 2
  $cl = (Get-Command claude -ErrorAction SilentlyContinue).Source; Run $hq "& '$cl' --agent channel-operator --model sonnet"; Start-Sleep 8; try { Hd agent rename $hq hq | Out-Null } catch {}
}

$agents = @(Get-Content "$F\agents.json" -Raw | ConvertFrom-Json) | Where-Object enabled
$wt = (Hd tab create --workspace $wsId --cwd $Repo --label 'Workers' --no-focus).result
$panes = @($wt.root_pane.pane_id)
for ($i = 1; $i -lt $agents.Count; $i++) {
  # grid: split the widest column right first, then down
  $src = $panes[[math]::Floor(($i - 1) / 2)]; $dir = if ($i % 2) { 'right' } else { 'down' }
  if ($i -eq 1) { $src = $panes[0]; $dir = 'right' } elseif ($i -eq 2) { $src = $panes[0]; $dir = 'down' } elseif ($i -eq 3) { $src = $panes[1]; $dir = 'down' }
  $panes += (Hd pane split $src --direction $dir --cwd $Repo --no-focus).result.pane.pane_id
}
for ($i = 0; $i -lt $agents.Count; $i++) { Run $panes[$i] (Cmd 'worker' $agents[$i].name) }
Hd tab focus $ctlTab | Out-Null
if ($Focus) { Hd workspace focus $wsId | Out-Null }
"$Label ready: workspace $wsId · Control tab (dashboard, controller, hq agent) · Workers tab ($($agents.name -join ', '))"
