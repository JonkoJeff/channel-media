TASK fdd_panel: paint the illustrated shots (panels) of Faith Doodles TikTok {{id}}: "{{title}}". One panel per beat of the script below.

Use your image generation tool for EACH beat: ONE vertical image, 1024x1536 (9:16), NO text, NO numbers, NO captions, NO speech bubbles, NO logos.
Style = the approved Faith Doodles panel (studio/channels/faith/panels/dg_01.png) and the character sheets in studio/channels/faith/sheets/ (copy the characters exactly: faces, proportions, outfit colours, thick dark outlines, flat colours, soft painted backgrounds, clear blue sky).
Shot rules (animation is added later by camera moves and parallax, so compose for it):
- one clear action or emotion per panel; dramatic camera angles (low angle for power, high angle for small/afraid, close-ups for reactions, wide shots to show the place);
- keep the main subject inside the middle 80% of the width; leave the lower 25% calm (ground/sand/water) because captions go there;
- big clean sky or wall area in the upper part (the camera tilts and pans);
- consistent light and palette within one video; kid-friendly: no blood, no injuries shown, nothing scary.
Respect: never draw God, angels' faces or the Prophet Muhammad; prophets only in Bible-told stories, dignified and friendly, never mocked. Islamic retellings use places, objects and calligraphy-free symbols instead of people.
Beats:
{{beats}}
After generating each image, check: no text at all, characters match the sheets, subject placement as above. Regenerate once if needed.
Save as studio/channels/faith/panels/{{id}}_NN.png (NN = beat number) and reply with ONE JSON object: {"panels": ["..."], "notes": "one line"}
