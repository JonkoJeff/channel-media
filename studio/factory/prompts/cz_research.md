TASK cz_research: market research for Cosmozibs (owner: Claude does this, Codex writes the scripts).

Inputs in your context pack: studio/trends/latest.json (topic group "cosmozibs"), studio/channels/cosmozibs/insights.md (our own numbers), series.json (queue).
1. Read the top outliers of the last 7 days in kids space/science (titles, thumbnails, length). Note per video: title formula, thumbnail (face/emotion, words, colors), hook.
2. Read our own numbers: which stories/hooks/thumbnail moods got the best CTR and retention, which Shorts the most views.
3. Output: (a) max 8 bullets "Now working" with example + outlier score, (b) the next 7 episodes for series.json (one per weekday theme, 4 stories each, each a single checkable fact, no repeat of an object used in the last 30 days), (c) 0-3 `PROPOSAL:` rules.
Never copy a title, thumbnail or script: take the pattern only.
Deliverable: JSON {"now_working": [...], "episodes": [{"id","day","title","stories":[4]}], "proposals": [...]}, first line `STYLE {{style_hash}}`.
