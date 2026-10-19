TASK cz_audit: audit Cosmozibs episode {{ep}} before rendering. You are the editor (Claude). Read the episode JSON.
Check and score 0-10: (1) every number traceable to a URL in `sources` (open 3 of them), (2) kid-friendly tone, nothing scary, (3) each Short 0..end works alone and ends on a punchline, (4) hooks varied, (5) thumbnail/cover text <= 3 words and not the title.
Run `python3 studio/cosmozibs/engine/validate.py studio/cosmozibs/episodes/{{ep}}.json` first; any error = fail.
Deliverable: first line `STYLE {{style_hash}}`, then `SCORE: n/10`, then max 6 concrete fixes as `FIX: <line index> <what>`. Pass = score >= 8 and no validator errors.
