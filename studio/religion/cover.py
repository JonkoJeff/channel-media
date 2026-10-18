"""Belief Through Time Short cover: the first 1.7 s of every Short is a designed thumbnail frame (Zernio takes the frame at 1.5 s),
so every Short has a real thumbnail: full-bleed artwork from the Short's first scene, dark gradient, big serif hook, last line on a coloured block.
Colour per Short (rotates gold / ember / teal / rose / ivory), never the same one twice in a row."""
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
ACC = [(232, 195, 106), (240, 120, 70), (80, 200, 190), (235, 110, 140), (240, 232, 214)]   # gold, ember, teal, rose, ivory

def cover(frame, title, n, path, ep=0):
    acc = ACC[(ep + n) % len(ACC)]; W, H = 1080, 1920
    im = Image.open(frame).convert("RGB"); r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS); x = (im.width - W) // 2; im = im.crop((x, 0, x + W, H))
    im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.15)).enhance(1.1)
    y = np.linspace(0, 1, H)[:, None]; k = 1 - 0.80 * np.clip(1 - y / 0.55, 0, 1) ** 1.4 - 0.65 * np.clip((y - 0.78) / 0.22, 0, 1)   # dark top (text) and foot
    im = Image.fromarray((np.asarray(im) * k[..., None]).clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(SERIF, 104); lines = []
    for w in title.upper().split():
        if lines and d.textlength(lines[-1] + " " + w, font=f) <= 940: lines[-1] += " " + w
        else: lines.append(w)
    lines = lines[:4]; yy = 170
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=f); L = (W - tw) / 2
        if i == len(lines) - 1 and len(lines) > 1:   # last line on a colour block
            d.rounded_rectangle((L - 26 + 10, yy + 6 + 10, L + tw + 26 + 10, yy + 138 + 10), 20, fill=(0, 0, 0))
            d.rounded_rectangle((L - 26, yy + 6, L + tw + 26, yy + 138), 20, fill=acc, outline=(0, 0, 0), width=6); d.text((L, yy), ln, font=f, fill=(24, 18, 12))
        else:
            d.text((L + 6, yy + 6), ln, font=f, fill=(0, 0, 0), stroke_width=12, stroke_fill=(0, 0, 0)); d.text((L, yy), ln, font=f, fill=(255, 255, 255), stroke_width=12, stroke_fill=(0, 0, 0))
        yy += 150
    g = ImageFont.truetype(SERIF, 44); t = "BELIEF THROUGH TIME"; tw = d.textlength(t, font=g)
    d.line(((W - tw) / 2, 1790, (W + tw) / 2, 1790), fill=acc, width=4); d.text(((W - tw) / 2, 1810), t, font=g, fill=acc, stroke_width=3, stroke_fill=(0, 0, 0))
    im.save(path, quality=93)

if __name__ == "__main__":
    import sys; cover(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4])
