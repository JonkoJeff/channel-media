TASK rel_cover: make the cover frame (thumbnail) of a Belief Through Time Short. It is shown full screen for the first 1.7 s of the Short and is the thumbnail of the post.
Episode {{ep}} "{{title}}". Short {{n}} of 4: "{{short}}"

Use your image generation tool to create ONE vertical image (1024x1536; it is cropped to 9:16 = 1080x1920, so keep everything important inside the middle 92% of the width).
The attached image is this episode's long-form thumbnail: the cover must look like its vertical sibling (same painting style, palette, light, gold serif lettering, same world), but show THIS Short's moment, not the same composition.

Layout:
- top third: the hook in big carved GOLD SERIF capitals, 2-4 short lines, max 6 words, centred, high contrast, inside the safe margins. Write the hook yourself from the Short's title: the surprising claim or question, in plain words (e.g. "A RIB... OR A SIDE?").
- middle and lower part: one clear focal subject from this moment: {{visual}}
- bottom: small serif mark "BELIEF THROUGH TIME" with a thin gold ornamental rule, above the lowest 8% (that strip is covered by the YouTube UI).
- no other text, no logos, no watermarks.
What is said in this Short (for the scene, do not write it on the image): {{say}}

Respect: no invented scripture quotes, no caricatures, no gore or graphic violence, never a depiction of the Prophet Muhammad{{extra}}.
After generating, look at the image: if any word is misspelled or extra text appeared, generate it once more with the fix.

Deliverable: ONE JSON object (no fences): {"hook": "the exact text on the image", "scene": "one line: what the image shows", "why": "one line"}
