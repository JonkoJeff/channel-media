TASK cf_plan: plan the next Crazy Facts long video `{{id}}`.

Pick ONE topic that is new (not in "Recent videos" or "Planned/used titles" in the pack), fits the channel promise, and follows learned rules and trends. Prefer a bigger cousin of what our numbers show works.
Choose the next format ONLY from F01, F02, F10, F15 (owner 22 Oct 2026: every BAD long video is at least 120 minutes, 11+ blocks); it must differ from the last two videos in structure. Never a format shorter than 120 min.

Deliverable: ONE JSON object (no fences), exactly these keys:
{
 "id": "{{id}}",
 "title": "...",                       // STYLE section 2 title rules, a different pattern than the last video
 "desc": "...",                        // 2-4 warm sentences, what we discover; ends with the cozy invitation; no chapter list
 "tags": ["#psychology", "..."],       // 6-8
 "format": "Fxx",
 "vibe": "calm",
 "voice": "am_michael",
 "playlists": ["..."],                 // one of: Your Brain, Explained | Sleep & Your Brain | Everyday Psychology | Memory & Mind Tricks | Fall Asleep Learning
 "thumb": {"text": "LINE1|LINE2", "sprite": "A..", "bg": "...", "mirror": false, "accent": "#RRGGBB"},
 "sources": [],
 "parts": ["{{id}}_b01", "..."],       // block count = format length / 11, rounded
 "plan": ["b01: ...", "..."]           // one line per block: the subtopic, the key study/fact to look for, the open loop it sets or pays off
}
The plan is what keeps parallel writers consistent: make every line specific (named study or phenomenon), make neighbouring blocks hand over naturally, block 1 = hook + "Tonight, we'll explore", last block = takeaways + callback + wind-down.
