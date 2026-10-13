# Codex task: write one Belief Through Time script
Fill in {{EP}}, {{TITLE}} and {{THUMB}}, then send this whole file to Codex (`codex exec -C <repo> -s workspace-write - < task`).

---
You write ONE narration script for the YouTube channel "Belief Through Time" (brand: Religion Unfolded).

Episode: {{EP}}
Title (exact, from studio/channels/religion/episode_list.md, without number): {{TITLE}}
Thumbnail already exists: {{THUMB}} (do not change it)
Output: write ONLY the file studio/channels/religion/stories/{{EP}}.txt. Do not edit, create or delete any other file. Do not run git.

Read first: studio/channels/religion/stories/FORMAT.md (exact file format), studio/channels/religion/stories/README.md (section "Production handoff": all rules apply), and the first 40 lines of studio/channels/religion/stories/21.txt as a format example (do not copy its content).

Requirements
- Length: at least 60 minutes of narration = 8,000-9,000 original spoken words (130 wpm). Timestamps are estimates at 130 wpm and must rise; each scene 6-20 s of speech (1-6 sentences).
- Header: TITLE, DESC (<= 4000 chars, neutral, with the chapter list as "hh:mm:ss name; ..."), TAGS (comma separated, include "Religion Unfolded, Belief Through Time"), SOURCES (real passages and real scholarly/museum sources only), SHORTS (exactly 4 lines `hh:mm:ss-hh:mm:ss | hook title`, each 35-58 s, starting and ending on scene timestamps, from different parts of the video), then a line `---`.
- 12-16 chapters (`CHAPTER: <name>` line before the scene where a chapter starts). First scene = a calm 20 s hook. Last scene ends softly.
- Tone: calm, warm, respectful documentary. Clearly separate what scripture says, what later tradition says, what historians/archaeologists say, and what is uncertain. Treat miracles and theological claims as claims of the tradition. Paraphrase scripture in your own words; no long quotations of modern translations. No mockery, no ranking of religions, no preaching, no shock hooks.
- Facts: never invent quotes, dates, names, events or sources. If you are not sure of a fact, leave it out.
- VISUAL lines: specific and searchable in public-domain archives (Wikimedia Commons, The Met, NASA, Library of Congress): name the artwork + artist, or the exact place/object/manuscript, in English (e.g. "The Deluge, Gustave Dore", "Ziggurat of Ur", "Hubble Ultra Deep Field", "Codex Leningradensis"). Vary them; do not repeat the same VISUAL more than twice. No artwork that shows God as a human figure; never any depiction of the Prophet Muhammad. SOURCE: one of wikimedia | met | smithsonian | rijksmuseum | loc | map | text-card.
- Forbidden: money/finance topics, invented facts, stage directions or timestamps inside NARRATION.

When done, reply with one line: `{{EP}}.txt: <words> words, <scenes> scenes, <chapters> chapters`.
