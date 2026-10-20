TASK cz_episode: write Cosmozibs episode {{ep}} "{{title}}" ({{theme}}) as ONE JSON file.

Stories (one per segment, in this order): {{stories}}
Next episode teaser: {{next}}

Follow studio/channels/cosmozibs/FORMAT.md exactly (it is in your context pack) and copy the structure of episodes/cz01.json.
- Research every fact with live web search. NASA / ESA / JPL first. Every number must come from a page you opened; put each URL in `sources`.
- ~1,150 spoken words in total so the long video lands at 8:05-8:20. Each story ~240 words incl. bonus fact and quiz.
- Lines 0..short.end of each story must work alone as a Short of 30-55 s (hook first, Rocky's punchline last).
- Use only the scene types listed in FORMAT.md. Change `show` every 1-2 lines.
- Write `thumb` and every `short.cover` per the thumbnail rules (<= 3 words, curiosity gap, never the title repeated).
- Add `description` (hook line, chapters left as {{chapters}}, sources, subscribe line, AI-voice line) and `tags` (3-5).

Deliverable: the JSON only, no fences, first line of your answer is `STYLE {{style_hash}}` and then the JSON.
Add `PROPOSAL:` lines after the JSON only if a rule or a missing scene type would clearly help.

- Add `"kw"` (TikTok search keyword, 2-5 lowercase words, no digits) to every story `short` and one top-level `"kw"` for the episode (FORMAT.md, "TikTok search keywords").
