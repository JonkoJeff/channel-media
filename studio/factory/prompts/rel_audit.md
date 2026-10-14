TASK rel_audit: you are the series editor of Belief Through Time. Check chapter {{n}} of {{total}} ("{{name}}") of episode {{ep}} "{{title}}" ({{tradition}}) against the style bible in the pack, as if one narrator made the whole episode.

Check: respectful tone (no mockery, ranking, preaching, shock); scripture / tradition / historians / uncertainty clearly separated in the wording; miracles framed as claims of the tradition; no invented quotes, dates or names (flag anything that looks invented); paraphrase instead of long quotations; VISUAL lines specific and allowed (STYLE section 3, including the Quran-episode rules); no part/chapter numbers or stage directions in NARRATION; hand-over fits the outline brief: {{brief}}

Chapter:
{{text}}

Deliverable: ONE JSON object (no fences): {"score": 0-10, "fix": true|false, "issues": ["concrete, fixable problem quoting the exact sentence or VISUAL", "..."]}
score >= 8 = publishable as is; fix = true only for problems a viewer or a member of that faith would notice, or a broken rule.
