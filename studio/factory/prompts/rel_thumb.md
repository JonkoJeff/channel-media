TASK rel_thumb: paint the YouTube thumbnail of Belief Through Time episode {{ep}}: "{{title}}" ({{tradition}}).

Use your image generation tool to create ONE landscape image, 1536x1024. It is cropped to 16:9 (1280x720): the top and bottom 8% are cut, keep everything inside.
Attached are 3 approved thumbnails of this channel (Q01 "Before Humanity", Q05 "Sun Moon Stars", 303 "The Great Leap"). Copy their FAMILY exactly (painting style, light, palette, lettering, layout), never their subject.

HARD RULES (an image that breaks one is rejected):
1. ONE focal subject, ONE painted cinematic scene: richly detailed, painted-photoreal, warm amber/golden rim light against deep navy and charcoal shadows. The subject sits inside the middle 70% of the width.
2. Headline: MAX 3 WORDS, in huge carved GOLD SERIF capitals exactly like the attachments (same letterforms in every Belief Through Time image), cap height at least 14% of the image height, high contrast, on a dark clean zone of the picture, never over a face, inside the safe margins. Headline: "{{headline}}" (if that is longer than 3 words, use its strongest 1-3 words).
3. The ONLY other text allowed is a small serif mark "BELIEF THROUGH TIME" (max 5% of the image height). NOTHING else: no verse or quote boxes, no scripture references, no citations, no numbers, no episode badge, no captions, no logos, no watermarks, no frames or panels, no collage.
4. Spell every word exactly.
Scene: {{visual}}
Episode (for the scene only, never write it on the image): {{desc}}

Respect: no invented scripture, no caricatures, no gore or graphic violence, never a depiction of the Prophet Muhammad{{extra}}.
After generating, look at the image and check rules 1-4. If one is broken, generate once more with the fix.

Deliverable: ONE JSON object (no fences): {"headline": "the exact headline on the image", "scene": "one line: what the image shows", "why": "one line"}
