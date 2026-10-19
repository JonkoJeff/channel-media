TASK cz_thumb: paint the YouTube thumbnail of Cosmozibs episode {{id}}: "{{title}}".

Use your image generation tool to create ONE landscape image, 1536x1024. It is cropped to 16:9 (1672x941 / 1280x720): keep everything important inside the middle 84% of the height.
Attached: studio/channels/cosmozibs/refs/thumb_example.jpg, the APPROVED Cosmozibs thumbnail (owner 19 Oct 2026). Copy its FAMILY exactly, never its subject:
- flat hand-drawn kids' doodle style: thick dark outlines, flat bright colours, deep navy/space background with small white dots as stars, no gradients-heavy 3D, no photo look.
- ONE huge hero object of THIS episode's theme (planet, star, black hole, volcano...) with a big expressive cartoon face (wide eyes, open mouth), filling about half the image, usually the right half.
- the crew character small and reacting (floating, surprised), with tiny yellow surprise strokes around it. Crew: Captain Cosmo (white astronaut suit, dark visor, orange gloves and boots, orange chest panel with red and teal dots, antenna with an orange ball), Zib (green one-eyed alien, purple iris, antennae), Bolt (grey boxy robot, blue screen face with ^ ^ eyes, red chest button, wheels), Rocky (grumpy grey asteroid with arms and legs), Tik (hourglass with face). Pick the one that fits.
- the headline is HAND-LETTERED as part of the drawing (chunky rounded bubble capitals with a dark outline, white + yellow like the example, slightly tilted, with yellow accent strokes), never a flat pasted text box. MAX 3 words, a curiosity question that adds to the title and never repeats it, big: cap height at least 14% of the image height, on the free side of the picture. Headline: "{{headline}}".
- optional: ONE tiny hand-written label with an arrow naming the object (like "NEPTUNE" in the example). NOTHING else: no logos, no channel name, no numbers unless they are the headline, no frames, no collage, no watermark.
Scene idea: {{visual}}
Episode (for the scene only, never write it on the image): {{desc}}
Kid-friendly: no scary injuries, nothing gross, cute not creepy.

After generating, look at the image: check spelling, the max-3-words rule, the style match with the attachment and that nothing important falls in the cropped top/bottom 8%. If one is broken, generate once more with the fix.
Save it as studio/channels/cosmozibs/thumbs/{{id}}.jpg (1280x720 or larger, 16:9, JPEG).

Deliverable: ONE JSON object (no fences): {"headline": "the exact text on the image", "scene": "one line: what the image shows", "why": "one line"}
