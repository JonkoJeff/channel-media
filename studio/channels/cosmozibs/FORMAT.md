# Cosmozibs episode format (the contract between Codex and the renderer)

One episode = one JSON file `studio/cosmozibs/episodes/czNN.json`. The renderer (`studio/cosmozibs/engine/build.sh czNN`) turns it into
1 long video (16:9, 8:05-8:20), 4 Shorts (9:16, max 58 s), 1 long thumbnail and 4 Short covers. Example: `episodes/cz01.json`.

## Top level
`id` (czNN) · `title` (<= 60 chars, number or question first) · `theme` · `next` · `sources` (every URL used) ·
`thumb` (see Thumbnails) · `description` · `tags` (3-5 topic tags; defaults are added) · `segments` (in order).

## Segments (fixed order)
`intro` (~45 s: crew hello, the 4 teasers, a `map` or `title` scene) → 4 story segments → `speed` (5 quick facts, optional) → `outro` (`pick` + next episode + subscribe).
A story segment has `short`: `{"title": "<= 50 chars hook", "end": <index of the punchline line>, "cover": {thumb spec}}`.
Lines 0..end are the Short: line 0 is the hook with its own `show`, the last one is a punchline (usually Rocky). Nothing in 0..end may refer to "earlier" or "this episode".

## Lines
`{"who": cosmo|zib|bolt|rocky|tik, "say": "...", "show": {scene}?, "sfx": scratch|boing|ding|pop?, "pause": 4?}`
- Max 25 words per line, max 12 words per sentence. Numbers written as words in `say` ("four hundred and sixty seven"), digits in `show`.
- `show` changes the picture; lines without `show` keep the last picture.
- Quiz: the question line has `"pause": 4` and a `quiz` show; the next line gives the answer with `"sfx": "ding"` and a new show.

## Roles
cosmo = host, opens every story with the hook · zib = asks "How could this happen?!", "That's crazy!" · bolt = numbers and comparisons ("I did the math!") ·
rocky = grumpy punchline at the end of each Short · tik = bonus facts, quiz, transitions ("Tick tock").

## Scene types (`show.type`) and fields
| type | fields | picture |
|---|---|---|
| title | text | big title with 4 planets |
| lineup | – | the crew big in the middle |
| map | hi: "venus,jupiter" or "none" | solar system, highlighted planets |
| planet | kind, label, zoom? | big planet with face; kinds: mercury venus earth mars jupiter saturn uranus neptune exo moon ganymede sun |
| versus | a, b, win?, label | two bodies side by side, crown on winner |
| thermo | value, label, compare | thermometer + oven |
| pressure | value, label | diver sinking with depth meter |
| daybar | a, av, b, bv, unit | two growing bars |
| quiz | q, options[3], answer | question cards + countdown |
| sunrise | – | sun rising in the west |
| dive | – | ship sinking into gas bands, CRUNCH |
| fill | count, label | outline filling with small Earths |
| bignum | value, label | big number with rays |
| wind | value, label | speed dial + wind streaks |
| sunlight | label | light beam Sun → far planet |
| glassrain | – | sideways glass rain |
| blanket · nomoon · acid · nightsky(label) · math · voyager(label) · daynight | – | special pictures |
| speed | n (0 = title card), planet, text | speed-round card |
| pick | – | 4 numbered planets |
A new scene type = a new function in `engine/scenes.part` (Claude adds it, never Codex).

## Thumbnails (`thumb` and `short.cover`)
`{"text": "<= 3 words, adds to the title, never repeats it", "planet": kind, "mood": scared|happy|none, "fx": [flames|shards|streaks|rocket], "char": cosmo|zib|bolt|rocky|tik, "bg": ["#hex", "#hex"]}`
Rules (research 19 Oct 2026): one big shocked face, max 3 elements, high contrast against YouTube's white/dark UI, readable at 320 px wide, curiosity gap (question, not answer), text top, character bottom-left, bottom-right kept free.
