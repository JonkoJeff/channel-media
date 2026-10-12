# Lessons

The machine adds a rule here every time a published video had a problem. Every new video must follow all rules.

## Rules
- AI images (Cloudflare Flux) refuse prompts with roses/romantic/pink + bedside wording as 'NSFW'; use neutral still-life words ("glass vase with garden flowers on a windowsill"). Check the screenshots run annotations for refused prompts before rendering: a missing photo file breaks the render.
- Every number, name and year on screen must match an opened source.
- A study's year is the year it was published. Say "published in 2000", never "in 2000 they ran", unless the source gives the year the experiment was run. (lf01: the T-shirt study ran in the late 1990s, published 2000.)
- Use the study's own measure in the line: if the paper measured "could recall/name the shirt", say "remembered", not "noticed". (lf01: 46% guessed vs 23% recalled.)
- Every Short's text ends with the AI disclosure line "Narration is AI-generated (synthetic voice)." after the tags. (sh01a went out without it.)
- A Short's text starts with a full sentence hook, not a fragment ending in a colon. (sh01a: "Your brain at 3 AM:".)
- `bars` scenes round values to whole numbers on screen: use them only for whole numbers; show decimals (e.g. 4.6%) in a `list`.
- Never put made-up "illustration" numbers in a `bars`/`stat` scene; if there is no measured number, use a `list`.

## Checked videos
checked: [lf01, sh01a]
- 2026-10-12: When the Cloudflare free AI quota is used up, photos.py falls back to Openverse with short queries. Those photos are often off-topic or show brands (Rolex, Harry Potter, Carnival). ALWAYS check a contact sheet and turn unsuitable photo segments into char segments before rendering. Budget ~40 AI images/day across both channels.
