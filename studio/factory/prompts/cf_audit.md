TASK cf_audit: you are the style editor. Check block `{{block}}` of "{{title}}" against the style bible and learned rules in the pack, as if one editor made the whole video.

Check: tone and narrator voice (STYLE 1-2), hook/story structure for its position ({{position}}), scene mix and the "every 60-90 s something changes" rule, no part numbers or stage directions, facts phrased per STYLE 9 (years = publication years, no invented numbers), image prompts per STYLE 5, consistent handover with the plan line: {{outline}}

Block:
{{text}}

Deliverable: ONE JSON object (no fences): {"score": 0-10, "fix": true|false, "issues": ["concrete, fixable problem with the exact sentence or segment", "..."]}
score >= 8 = publishable as is; fix = true only for problems a viewer would notice or that break a rule.
