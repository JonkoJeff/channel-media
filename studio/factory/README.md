# Factory: one queue, many agents, one editor

Runs locally in Herdr (workspace "CrazyFacts HQ"). Start: `pwsh -File studio/factory/hq.ps1`.

## Who does what
| Work | Primary | Failover | Why |
|---|---|---|---|
| Video plan (topic, title, format, block outline, thumb idea) | Codex/ChatGPT | Claude | text work on the ChatGPT subscription |
| Script blocks (~1,650 words each, written in parallel, live web search for facts) | Codex | Claude after 20 min waiting | parallel lanes = a 14-block video in ~1 h instead of ~7 h |
| Style audit per block (one editor) | Copilot (off: no CLI access) -> Claude Haiku | Codex | cheap, independent second eye |
| Fix after a failed audit (one round) | Codex | Claude | |
| Shorts: exact segment ranges, hooks, titles, ranked by virality | Codex | Claude | segment boundaries are the exact cut points |
| Final thumbnail spec | Claude | Codex | variety + trend rules + learned rules |
| BTT long thumbnail without owner art (`rel_thumb`), cover frame per Short (`rel_cover`, `cf_cover`) | Codex (image generation) | none: a failed cover falls back to the drawn one | same look as the channel's long-form thumbnails; `codex_covers` in config.json switches covers off |
| Performance analysis -> learned rules for everyone | Claude | Codex | the single gatekeeper of style changes |
| Block JSON, B-roll, render | GitHub Actions (`factory.yml` -> `render-long.yml`) | | no tokens |
| QC + scheduling + posting | channel-operator (Claude) | | never delegated |

## How it stays efficient
- **Watermarks**: the controller counts long videos that are still to air, rendered but unscheduled, or in production. Below `low_watermark` it starts generating; at `high_watermark` it stops. Nothing is generated "just because".
- **Pull model**: idle workers pull the next task they may do; no dispatcher waits. A finished block immediately unlocks its audit (no polling gap).
- **Failover**: every worker writes a heartbeat; a silent worker's task returns to the queue within 2 min and goes to another agent (the failed agent is avoided). Timeouts and stalls (no output) kill the run. Rate limits put an agent in a 60 min cooldown, 3 failures in a row in 15 min. Fallback kinds may take a task once it waited `spill_after_s` or when no preferred agent is alive.
- **Tokens**: agents run headless and read-only; the worker writes the files. The context pack (~4k tokens) replaces reading the repo. Exact token usage per task (Codex JSON, Claude stream-json) goes into `state/events.jsonl` and the dashboard. Per-agent daily caps.

## How it stays one editor
- `STYLE.md` is the source of truth; `learned.md` holds rules learned from real numbers. The context pack (STYLE + learned + lessons + trends + our numbers + recent videos + allowed sprite/background pairs) is rebuilt for every task and versioned by hash.
- Every deliverable must start with `STYLE <hash>`; a deliverable made against an old version is rejected, so no agent works from stale rules.
- Agents never change style themselves: they add `PROPOSAL:` lines; only the analyst promotes them into `learned.md`, so everyone learns the same thing at the same moment. `REQUEST:` lines let an agent ask another agent for work (allowed types in config.json, rate limited).
- A validator checks every block (allowed sprite/background pairs, scene fields, char runs, photos, length, no part numbers) and an audit checks tone and structure before anything is rendered.

## Commands (`pwsh -File studio/factory/factory.ps1 <mode>`)
`status` · `dash` · `controller` · `worker -Name codex1` · `new-video` · `covers -Id lf15,rel24` (Codex covers for already scheduled Shorts, pushed and re-attached via zernio rethumb) · `enqueue -Type cf_audit -Arg '{"id":"lf12","block":"lf12_b03"}'` · `add-agent -Name codex3 -Kind codex` · `pause` · `resume` · `retry -Id <task>` · `kill -Id <task>` · `pack`

## Adding an agent
`factory.ps1 add-agent -Name codex3 -Kind codex` (or `claude` with `-Model haiku|sonnet`): it is added to agents.json and, when HQ runs, gets its own pane in the Workers tab. New kinds need one `switch` branch in `Run` (factory.ps1).
