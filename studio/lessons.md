# Lessons

The machine adds a rule here every time a published video had a problem. Every new video must follow all rules.

## Rules
- AI images (Cloudflare Flux) refuse prompts with roses/romantic/pink + bedside wording as 'NSFW'; use neutral still-life words ("glass vase with garden flowers on a windowsill"). Check the screenshots run annotations for refused prompts before rendering: a missing photo file breaks the render.
- Every number, name and year on screen must match an opened source.
- A study's year is the year it was published. Say "published in 2000", never "in 2000 they ran", unless the source gives the year the experiment was run. (lf01: the T-shirt study ran in the late 1990s, published 2000.)
- Use the study's own measure in the line: if the paper measured "could recall/name the shirt", say "remembered", not "noticed". (lf01: 46% guessed vs 23% recalled.)
- Every Short's text ends with the AI disclosure line "Narration is AI-generated (synthetic voice)." after the tags, on every route (Metricool and Zernio). (sh01a and the Zernio Short Z1u8rdbwEcQ / sh08_01 went out without it; zernio.py now adds it.)
- A Short's text starts with a full sentence hook, not a fragment ending in a colon. (sh01a: "Your brain at 3 AM:".)
- `bars` scenes round values to whole numbers on screen: use them only for whole numbers; show decimals (e.g. 4.6%) in a `list`.
- Never put made-up "illustration" numbers in a `bars`/`stat` scene; if there is no measured number, use a `list`.
- Photo credits (CC BY / BY-SA) in a description always keep author, license and link; to fit YouTube's 5,000 characters shorten the photo title or the source lines, never the credit. CC0/PDM photos go on one line "Other photos: public domain". (lf08's scheduled text had credits cut to "by Ciara Ní Riain (wikimed…"; fixed before publishing, longform.py now does this.)
- Before starting a render, check that every `photo` file of the video exists in `photos/`. If the Cloudflare quota was used up (screenshots run warning "429 ... daily free allocation"), dispatch `screenshots` with `fallback` = the video's file prefix (e.g. `lf09_`), then check the contact sheet. (lf09: all 29 AI images were missing.)
- Openverse fallback photos for lf09: 18 of 29 were off-topic or unusable (10 Downing Street letterhead, American Airlines toy, newspapers, identifiable children, Chichen Itza for "a garden path"); they became char scenes. Write AI prompts early in the UTC day, and never fetch more than ~30 AI images per day for all channels together (lf09-lf11 + mn02 in one night used up the quota).
- Keep max 3 `char` scenes in a row (B3). lf07-lf09 have runs of 5-13 (wind-down 13-22); new scripts must break runs with `list`, `quote`, `stat`, `curve` or `photo` scenes.
- While long videos go out via Metricool, start the render with input `metricool=1` (720p, max 500 MB); the default encode is Zernio 1080p (~1.5 GB) and Metricool rejects it.
- Belief Through Time descriptions never contain internal production notes ("Estimated chapters ... align to audio" + estimated timestamps). rel21 went out with them; religion/build.py now strips everything from "Estimated chapter" on in DESC.
- Brain After Dark: the calm re-frame must never crop the left caption card. lf13 (render 15 Oct) had 4 of 12 review frames with the caption cut off by the close shot (z 1.13, shift +210); longform.py close shot is now left-anchored (z 1.11, shift -400). A render with a cut caption in any review frame fails QC: set "hold" in result.json (autoplan skips it) and re-render.
- Brain After Dark descriptions: Sources must be one clean line per source (no raw {'title':...} dicts, no duplicates). lf13's description had 21 duplicated/raw lines; fixed by hand before scheduling.
- Never dispatch render-long in the same minute as the push that adds new #ai photos: the screenshots workflow commits the images ~2 min later, and a render that checked out before that commit fails on every part with FileNotFoundError (lf20, 24 Oct: whole render lost, 22/25 Oct without a fresh BAD long video). Wait for the "Screenshots" commit, confirm every photo file exists, then dispatch.

## Checked videos
checked: [lf01, sh01a, lf06, sh08_01]
- 2026-10-12: When the Cloudflare free AI quota is used up, photos.py falls back to Openverse with short queries. Those photos are often off-topic or show brands (Rolex, Harry Potter, Carnival). ALWAYS check a contact sheet and turn unsuitable photo segments into char segments before rendering. Budget ~40 AI images/day across both channels.
- 2026-10-12: lf06 (7eBMzF04nVA, published 11 Oct 20:00) checked: title OK, public, AI disclosure line present, no chapter list (calm rule). Source lines are cut with "…" (author + year kept). Re-checked 3 claims: Aserinsky & Kleitman 1953 in Science (eye movements under the eyelids), Sharpless & Barber 2011 review of 35 studies with 36,533 people, Randy Gardner awake Dec 28 1963 to Jan 8 1964, ~264 h, Guinness stopped tracking (NPR 2024). All correct.
