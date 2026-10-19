TASK cz_cover: paint the cover frame (thumbnail) of a Cosmozibs Short. Long video "{{title}}" ({{id}}). Short {{sid}}: "{{short}}"

Use your image generation tool to create ONE vertical image (1024x1536; it is cropped to 9:16 = 1080x1920, keep everything important inside the middle 92% of the width).
Attached: studio/channels/cosmozibs/refs/thumb_example.jpg (the approved style) and this episode's long thumbnail studio/channels/cosmozibs/thumbs/{{id}}.jpg when it exists. The cover is a vertical sibling of them: same flat hand-drawn kids' doodle style, thick outlines, navy space with white dot stars.
- ONE huge hero object of THIS Short's story with a big expressive cartoon face in the middle, and one small reacting crew member (same designs as in the attachments; never redesign them).
- top third: the hook HAND-LETTERED as part of the drawing (chunky bubble capitals, white + yellow, dark outline, yellow accent strokes), max 3 words: "{{hook}}". Never a pasted text box.
- the lowest 10% stays free of text (YouTube/TikTok UI). No other text, no logos, no watermarks.
What happens in this Short (for the scene, never write it on the image): {{say}}

After generating, check spelling, word count and style; fix once if needed. Save it as studio/covers/{{sid}}.jpg (9:16 JPEG).

Deliverable: ONE JSON object (no fences): {"hook": "the exact text on the image", "scene": "one line", "why": "one line"}
