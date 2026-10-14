TASK cf_shorts: pick the Shorts for the Crazy Facts video "{{title}}" ({{id}}).

Below is every segment of the video: `[block #index ~mm:ss within block | type] voice line`. Times are estimates; the cut points (segment boundaries) are exact after rendering.
Choose {{count}} Shorts (STYLE section 8): the most gripping, self-contained 25-58 s moments: hooks, surprising numbers, counter-intuitive results, "you do this too" moments, myth flips. At most one Short per block. Rank them: the strongest first (it is posted first).

Segments:
{{digest}}

Deliverable: ONE JSON array (no fences), strongest first, each:
{"src": "<block id>", "first": <segment index>, "last": <segment index>, "start": "mm:ss", "end": "mm:ss", "top": "full-sentence hook, max 45 chars", "title": "max 60 chars", "tags": ["#shorts", "#psychology", "#..."], "why": "hook/retention reason in a few words"}
first..last must be 25-58 s of speech (about 65-150 words) and start on the hook sentence.
