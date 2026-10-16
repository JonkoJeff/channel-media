TASK rel_thumb: make the YouTube thumbnail for Belief Through Time episode {{ep}}: "{{title}}" ({{tradition}}).

Use your image generation tool to create ONE landscape image (1536x1024 or wider; it is cropped to 16:9 = 1280x720, so keep everything important inside the middle 90% of the height).
The attached images are approved thumbnails of this channel: match their family exactly, do not copy their subject.

Style (STYLE: thumbnail family):
- cinematic, richly detailed painted-photoreal historical scene; warm amber/golden rim light against deep navy and charcoal shadows; one clear focal subject; depth and atmosphere.
- headline in big carved GOLD SERIF capitals (like the attachments), 2 lines max, legible at phone size, inside the safe margins, never over a face: "{{headline}}"
- small ornate serif mark "BELIEF THROUGH TIME" with a thin gold ornamental rule, top-left; a small framed gold episode badge "{{ep}}" top-right.
- no other text, no logos, no watermarks, no numbered grid or collage look.
Scene: {{visual}}
Episode summary (for the scene, do not write it on the image): {{desc}}

Respect: no invented scripture quotes, no caricatures, no gore or graphic violence, never a depiction of the Prophet Muhammad{{extra}}.
After generating, look at the image: if any word is misspelled or extra text appeared, generate it once more with the fix.

Deliverable: ONE JSON object (no fences): {"headline": "the exact headline on the image", "scene": "one line: what the image shows", "why": "one line"}
