# Crazy Facts: the style bible (single source of truth)

Every agent (Claude, Codex/ChatGPT, Copilot, any agent added later) works from this file plus the generated context pack. Together they behave like ONE editor: a viewer must never be able to tell that several agents worked on a video. Consistency beats speed. When this file and an older note disagree, this file wins; when the owner says something new, it goes here (or into learned.md) first.

## 1. Identity
- Channel: Crazy Facts (YouTube "Crazy_Factsss"). English. Psychology explained: why your brain does the odd, everyday things it does.
- Promise: one surprising, true, sourced idea, told warmly so the viewer feels smarter and a little seen. Never clickbait the video does not deliver.
- Narrator voice: a friendly, curious guide talking to ONE person ("you"). Warm, a little playful, never hype, never preachy, never shouting.
- Character: the approved chibi (sprite prefix A, red hoodie) is the face of the channel. One character family per video; never mix two characters in one video.
- Forbidden on every channel: money/finance topics, invented facts/numbers/quotes, copyrighted music/clips/lyrics, real people as AI images, brands/logos, reused scripts with a swapped topic.

## 2. Long-video format (current strategy)
- Vibe `calm` for long videos: unhurried sentences, cozy, warm backgrounds, calm sprites (HAPPY, NEUTRAL, THINKING-type; never SHOCKED/ANGRY/panic). The renderer then applies: calm voice (am_michael), longer pauses, warm grade, crossfades, no sound effects, soft amber captions.
- Rotate the 15 formats (F01-F15 in RUNBOOK "VARIETY"); the next video must differ from the last two in length AND structure. Blocks are ~11 min (~1,500-1,800 words); number of blocks = format length / 11.
- One topic, one flowing story. Viewers never see parts: no "Part one", no part numbers, no "in this part". Block boundaries are invisible; transitions are spoken ("Now, let's go a little deeper...").
- Title: short, curiosity first, max ~45 characters. Patterns that work (rotate): "Why We [everyday behaviour]", "Why Some People [odd habit]", "Your Brain on [X], Explained", "The Psychology of [X], Explained", "What [X] Really Does to Your Brain". Never repeat the previous video's pattern.

## 3. Story and hook structure (every block)
- Block 1, first 15 s: a gentle hook that opens a curiosity gap (a relatable moment + "here's what's really going on"), then a `list` "Tonight, we'll explore" (no numbers). Never a fake cliffhanger.
- Each subtopic = mini-arc: relatable moment -> question -> the study/evidence (who, where, what, published year) -> what it means for you -> a soft bridge to the next idea.
- Every 60-90 s of speech something changes on screen (new scene type, new sprite pose, a stat, a photo). This is our main retention tool.
- Open loops: tease one later answer early in a block and pay it off before the block ends.
- Last block: practical takeaways, a callback to the opening moment, a gentle guided wind-down (`speed 0.8, pause 1.6` is set by the pipeline for wind-down blocks), then the `end` segment teasing the next video.

## 4. Scene grammar (compact format, parsed by studio/scripts/block.py)
Segments are separated by a blank line. Line 1 = header, following lines = the voice line.
```
@char SPRITE BG | cap | sub            @chapter SPRITE BG | title           @end SPRITE BG | next title
@list SPRITE BG | title | a ;; b ;; c  @study SPRITE BG | who | where | what @stat SPRITE BG | title | big | label
@bars SPRITE BG | title | unit | lab:val ;; lab:val                     @quote SPRITE BG | text | by
@curve SPRITE BG | title | x | y | peak | label                         @photo FILE | cap
#ai FILE | prompt          (adds an AI B-roll image; put these lines in their own segment block)
```
- Only approved sprites and backgrounds, and only allowed pairs (sprite emotion must be in the background's emotion list). The context pack lists every allowed pair; anything else blocks the render.
- Mix per block: at least 1 `photo`, plus `list`, `study`, `stat`, `bars`, `curve`, `quote`; never more than 3 `char` scenes in a row; lead each block with a different sprite/background than the previous block.
- `bars` show whole numbers only; decimals go in a `list`. Never invented "illustration" numbers in `bars`/`stat`.
- `chapter` segments in calm videos show only their title as a quiet caption; their voice line is a natural transition.
- Voice lines: 1-6 sentences, spoken English, no stage directions, no timestamps, years in digits.

## 5. B-roll and images
- `#ai FILE | prompt`: file name `<blockid>_NN.jpg`. Describe scene, style, light, mood, and end with "no text, no logos". Never real people, brands, copyrighted characters or our own character. Neutral still-life words (Cloudflare refuses romantic/bedside wording).
- Budget: max ~2 AI images per block, ~30 per day for all channels together.
- Proof (studies, prices, dashboards) is never an AI image: use `study`/`stat`/`list` cards.

## 6. Captions, sound, motion (automatic: do not specify)
- Word-by-word captions, scene transitions, character motion, drifting backgrounds, warm grade and loudness (-16 LUFS) are done by the renderer from the vibe. Non-calm (Shorts/energetic) renders get punch-in transitions, white flash on chapters, pop/whoosh/boom sfx per scene type. Agents only choose scene types and sprites; they never write sfx/zoom instructions.

## 7. Thumbnails
- `thumb` = `{text: "LINE1|LINE2", sprite, bg, mirror?, accent?}`. Max 3 words in total, 2 lines; the text is the emotional twist and ADDS to the title, never repeats it ("IT NEVER|SLEEPS", "SO|BORED").
- One big expressive sprite whose emotion matches the twist; it may hold the topic as a metaphor (trend R7). Sprite ALWAYS left, text right (owner 23 Oct 2026: the YouTube duration badge sits bottom-right and covered the sprite); longform.thumbnail() forces this, `mirror` is ignored.
- Variety: never the same sprite, background, accent colour or layout as the previous upload. Use light accent colours (text on the block is dark). Recently used ones are in the context pack.

## 8. Shorts (cut from the long video at render time)
- Each Short is an exact segment range of one block: `{id, src: "<blockid>", first, last, top, title, tags}`. Cut points ARE segment boundaries, so timestamps are exact once rendered.
- 25-58 s of speech (~65-150 words), self-contained: starts on the hook sentence, ends on the payoff (no dangling "and then...").
- Pick the strongest moments: a surprising number, a counter-intuitive study result, a "you do this too" moment, a myth flip. Prefer segments with a `stat`/`study`/`bars` card inside (visual payoff).
- `top` = a full-sentence hook (never a fragment ending in ":"), max ~45 characters. `title` = curiosity, max ~60 characters, no clickbait. Tags: "#shorts", "#psychology" + 1-2 topic tags.
- About one Short per block, never two from the same block in a row on the schedule.

## 9. Facts
- Every number, study, name and year comes from a real source the writer is confident about; list it under SOURCES. Unsure -> leave it out.
- A study's year is its publication year ("published in 2014"). Use the study's own measure ("remembered", not "noticed").

## 10. How agents stay one editor
- Read the context pack first (it contains this file, learned rules, lessons, trends, our numbers and the last videos). The pack's STYLE version must be the first line of every deliverable.
- Never invent a personal style. If you think a rule should change, add a line `PROPOSAL: <rule> because <evidence>` after your deliverable. Only the analyst (Claude) promotes proposals into learned.md, so every agent learns the same thing at the same moment.
- To ask another agent for work, add `REQUEST: {"type": "cf_fix", "args": {...}, "reason": "..."}` after your deliverable.
