# Crazy Facts channel machine
This repo runs an automated faceless YouTube channel (English psychology explainers with an approved chibi character).
For any scheduled or manual run: follow `studio/RUNBOOK.md` exactly. Use the ponytail skill (smallest complete change, reuse first).

## BOTH CHANNELS ACTIVE (owner, 15 Oct 2026, replaces the earlier "FOCUS: Brain After Dark only")
Beide kanalen actief: 1 lange video + 4 Shorts per dag per kanaal, geen geld/finance-content, nooit twee keer uploaden. BAD is de standaard, BTT wordt ernaar opgetrokken.
- Brain After Dark (BAD, formerly "Crazy Facts", Zernio key 1, zernio.json youtube.crazyfacts) and Belief Through Time (BTT, religion, second YouTube account of Zernio key 1, zernio.json youtube.religion).
- Schedule for both (Europe/Amsterdam): long video 20:00, Shorts 15:00, 18:00, 21:00, 23:30. Never schedule beyond the buffer.
- BTT catches up with BAD per studio/channels/religion/GAP.md (voice, thumbnails, editing, hooks, variety, growth loop, localization).
- Codex/ChatGPT writes texts and researches growth; Claude validates, renders, QC, posts and turns findings into rules in studio/factory/learned.md (with the channel name).

## Priorities (owner)
Execution > Discussion. Speed > Research. Consistency > Volume. Repository state > chat memory (state lives in files, never in the conversation).

## Factory in herdr (owner, 13 Oct 2026, replaces the routing below where they conflict)
Crazy Facts long videos are made by the factory: `studio/factory/README.md`. Herdr workspace "CrazyFacts HQ" (`pwsh -File studio/factory/hq.ps1`) shows the dashboard, the controller, the hq agent and one pane per worker. Codex writes plans, script blocks and Shorts cuts; Claude does thumbnails, audits, analysis and is the failover writer (owner: tasks must never hang, another agent takes over). Style source of truth: `studio/factory/STYLE.md` + `learned.md`. The factory stops generating when the buffer is full and pushes finished scripts to `factory.yml` for rendering; QC and posting stay here (channel-operator).

## Multi-agent routing in herdr (owner, 13 Oct 2026)
Run Claude Code inside a herdr pane; herdr only lets agents control herdr from inside a herdr pane. Codex (ChatGPT subscription) and Copilot (free) are signed in and connected; check with `herdr integration status`. Use `herdr agent start <name> --kind codex|copilot`, send a task, wait until it is done, then `herdr agent read`; see `herdr agent --help` for exact flags (never guess flags).
- Claude keeps: render pipeline (studio/religion/build.py, render-long, shorts), render QC, Zernio posting/deleting, keys, accounts, priorities, RUNBOOK, fixing failures.
- Codex/ChatGPT: scripts `studio/channels/religion/stories/NN.txt` (FORMAT.md), titles, descriptions, tags, Short hooks, thumbnail text, fact check with sources.
- Copilot (free, weaker): queue/list upkeep, JSON metadata, small script edits that Claude reviews.
- Each task = one self-contained instruction (input file, output file, format, forbidden topics) and one file back. Claude validates with a script, samples content, allows ONE correction, then takes over or reports.
- No other agent gets keys or may publish/delete. Keys only as GitHub Actions secrets (never in repo or CLAUDE.md). Images (owner 16 Oct 2026): Codex paints the BTT long thumbnails that have no owner art (factory `rel_thumb` -> studio/channels/religion/thumbs/NN.jpg) and the cover frame of every Short of both channels in that channel's long-form thumbnail style (`rel_cover`/`cf_cover` -> studio/covers/<short id>.jpg: first 1.7 s of the Short + post thumbnail). BAD long thumbnails stay the drawn pipeline (approved sprites). Copilot cannot make images.
- Model: Sonnet by default (`/model`); Opus only for a real design decision. Rendering runs in GitHub Actions: start, wait in one loop, read one line.
- Never any money/finance content. Only channels: Belief Through Time (priority) and Crazy Facts.
