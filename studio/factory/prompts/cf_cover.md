TASK cf_cover: make the cover frame (thumbnail) of a Brain After Dark Short. It is shown full screen for the first 1.7 s of the Short and is the thumbnail of the post.
Long video "{{title}}" ({{id}}). Short {{sid}}: "{{short}}"

Use your image generation tool to create ONE vertical image (1024x1536; it is cropped to 9:16 = 1080x1920, so keep everything important inside the middle 92% of the width).
Attached: first a long-form thumbnail of this channel (the style to match exactly), then the approved character pose to use. The cover must look like a vertical sibling of the long-form thumbnail:
- the SAME chibi character as in the attachments (same face, hair, outfit, line art and colouring; do not redesign or restyle the character), large in the lower half, with a white sticker outline and a soft glow in the accent colour {{accent}}.
- background: a blurred warm cosy scene ({{bg}}), darkened towards the edges.
- top third: the hook in heavy bold sans-serif capitals (like the attachment): white letters with a thick black outline, the LAST line inside a rounded block in {{accent}} with dark letters; 2-4 lines, max 6 words, centred, inside the safe margins. The Short's hook is "{{hook}}": use it as is when it has 6 words or fewer, otherwise shorten it to max 6 words that keep the claim (e.g. "CAMP WAS A SECRET TEST").
- the lowest 8% stays free of text (covered by the YouTube UI). No other text, no logos, no watermarks.
What is said in this Short (for the expression and scene, do not write it on the image): {{say}}

After generating, look at the image: if any word is misspelled, extra text appeared or the character looks different from the attachment, generate it once more with the fix.

Deliverable: ONE JSON object (no fences): {"hook": "the exact text on the image", "scene": "one line: what the image shows", "why": "one line"}
