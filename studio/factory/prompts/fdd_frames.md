TASK fdd_frames: draw a frame-by-frame animation sequence for Faith Doodles character "{{char}}", action "{{action}}" ({{frames}} frames).

Use your image generation tool to create ONE image, 1536x1024, plain cream background (#fdfbee), no grid lines, no numbers, no text, no shadows touching each other.
Attached: the approved pose sheet of {{char}} (studio/channels/faith/sheets/). Copy the character EXACTLY: same face, proportions, outfit colours, thick dark outline, flat colours. Never redesign.
Layout: {{frames}} drawings in reading order, left to right, top to bottom, evenly spaced, each fully separate (at least 40 px of empty cream between drawings), all the same size and the same ground line per row.
The drawings are consecutive animation frames with real in-betweens (classic 2D cartoon, animated "on twos"): small, smooth changes from one frame to the next, with anticipation, overlap and follow-through (hair, robe and bag swing a little after the body).
Action: {{action_desc}}
Respect: never draw God or the Prophet Muhammad; prophets only as in a children's Bible, friendly and dignified, never comic or humiliating.
After generating, check: same character in every frame, {{frames}} separate drawings, no text. If not, generate once more with the fix.
Save as studio/channels/faith/sheets/{{char}}_{{action}}.png and reply with ONE JSON object: {"file": "...", "frames": N, "notes": "one line"}
Typical actions: walk (8 frames, one full cycle), run (8), throw/sling (6: wind-up, swing, release, follow-through), fall (6: hit, stagger, tip, fall, land, dizzy), talk (4: small mouth/hand variations), point (4), cheer (6).
