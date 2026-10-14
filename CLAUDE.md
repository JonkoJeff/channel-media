# Crazy Facts channel machine
This repo runs an automated faceless YouTube channel (English psychology explainers with an approved chibi character).
For any scheduled or manual run: follow `studio/RUNBOOK.md` exactly. Use the ponytail skill (smallest complete change, reuse first).

## FOCUS: BRAIN AFTER DARK ONLY (owner, 15 Oct 2026, overrides every Belief Through Time line below and in RUNBOOK/agents)
Belief Through Time / Religion Unfolded is STOPPED: no new scripts, renders or posts. All energy goes to Brain After Dark (YouTube channel, formerly "Crazy Facts", handle @BrainAfterDark, Zernio key 1). Growth first: ChatGPT/Codex writes texts and researches YouTube growth strategy from videos and online sources; Claude validates, renders, QC, posts and turns findings into rules in studio/factory/learned.md. The daily-video rule for Belief Through Time is void. Already scheduled Belief Through Time posts stay unless the owner says delete.

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
- No other agent gets keys or may publish/delete. Keys only as GitHub Actions secrets (never in repo or CLAUDE.md). Codex/Copilot cannot make images: thumbnails come from the existing pipeline.
- Model: Sonnet by default (`/model`); Opus only for a real design decision. Rendering runs in GitHub Actions: start, wait in one loop, read one line.
- Never any money/finance content. Only channels: Belief Through Time (priority) and Crazy Facts.
