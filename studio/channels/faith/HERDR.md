# Faith Doodles: full run for Claude Code in herdr (owner, 21 Oct 2026)

Work on branch `cosmozibs` of channel-media (`git fetch && git checkout cosmozibs && git pull`). You run in a herdr pane; Codex is available (`herdr integration status`; see `herdr agent --help` for exact flags, never guess).
Channel: Faith Doodles, TikTok only (@jv.clipssss, Zernio key 2 = channel `faith`). English. Painted-shot style only (never the old Sam/doodle-engine style). Every video at least 60 seconds.

## 1. Paint the shots with Codex
Read `studio/channels/faith/codex_requests/BATCH_01.md`. Start one Codex agent task per episode (fddp03-fddp07) with that file's instructions and the episode JSON. Each task returns 12 PNGs named exactly like the `panel` fields. Check every image yourself (Read): 9:16, no text, matches THE MODEL. One retry per bad image, then repaint it with another Codex task. Commit the PNGs to `studio/channels/faith/panels/` and push.

## 2. Render (GitHub Actions, no tokens)
For each episode whose 12 panels are pushed: `gh workflow run cosmozibs.yml --ref cosmozibs -f ep=<id> -f mode=panels` (one at a time is fine, they can run in parallel). It renders the 60+ s TikTok with the Chatterbox voice, layered camera animation and captions, and publishes release `<id>` with `<id>.mp4`.
Download one with `gh api -H "Accept: application/octet-stream" repos/JonkoJeff/channel-media/releases/assets/<asset id>` and spot-check it (duration >= 60 s, 1080x1920, voice + captions in sync).

## 3. Schedule on TikTok (10 a day)
`gh workflow run zernio.yml --ref cosmozibs -f cmd=faith -f a=fddp02,fddp03,fddp04,fddp05,fddp06,fddp07` (ids with a finished release only). It fills the next free slots (10 a day, US Eastern) and records them in `studio/channels/faith/posted.json`; an id is never posted twice. Wait for each zernio run before starting the next (concurrency group).

## 4. Keep it running (daily)
- Keep at least 20 rendered, unscheduled videos ready (10 a day). When fewer: write new episode JSONs in the same format as fddp03 (12 lines, 150-180 words, one panel per line, hook + title + kw, sources), new story ids `fddpNN`, then repeat steps 1-3.
- Story pool (Bible first, then other faiths respectfully): Adam and Eve, Cain and Abel, Tower of Babel, Abraham and the stars, Isaac, Jacob and Esau, Jacob's ladder, Joseph, baby Moses, burning bush, the ten plagues, Red Sea, Ten Commandments, Jericho, Gideon, Samson, Ruth, Samuel, David and Goliath, Solomon's wisdom, Elijah and the fire, Daniel and the lions, Esther, Jonah, birth of Jesus, the wise men, Jesus calms the storm, feeding the 5,000, walking on water, the Good Samaritan, the prodigal son, Zacchaeus, the lost sheep. Other faiths: tell them through places and objects (no prophets drawn in Islamic retellings, never the Prophet Muhammad, never God).
- Facts: every story from the text named in `sources`; kid-friendly; no violence shown.
- Report to the owner after each run: what was painted, rendered, scheduled, and what failed.
