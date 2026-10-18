"""BTT Short cover = text-free painted art + headline in the long thumbnails' lettering (cream-gold serif, ornament rules, small brand mark).
Codex paints only the picture; the lettering is drawn here so it is always spelled right, centred, in the same style and >= 12% of the height.
usage: python cover_text.py art.jpg "HOOK TEXT" out.jpg [--blur-bars]"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1920
FONTS = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Cinzel.ttf"), r"C:\Windows\Fonts\cambriab.ttf", r"C:\Windows\Fonts\palab.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
FONT = next(f for f in FONTS if f and os.path.exists(f))   # Cinzel (OFL, Trajan-style capitals) = the long thumbnails' lettering
def F(size):
    f = ImageFont.truetype(FONT, size)
    if FONT.endswith("Cinzel.ttf"): f.set_variation_by_axes([800])
    return f
CREAM, GOLD, AMBER = (252, 238, 205), (226, 176, 92), (120, 70, 20)

def fit(d, txt, maxw, hi=420, lo=120):
    for s in range(hi, lo - 1, -4):
        f = F(s)
        if d.textlength(txt, font=f) <= maxw: return f
    return F(lo)

def lines_of(words):
    return words[:3]   # one word per line, stacked, so every line can be as big as the width allows (long thumbnails: stacked words)

def cover(art, hook, out):
    im = Image.open(art).convert("RGB"); r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS); x = (im.width - W) // 2; y0 = (im.height - H) // 2
    im = im.crop((x, y0, x + W, y0 + H))
    y = np.linspace(0, 1, H)[:, None]; k = 1 - 0.62 * np.clip(1 - y / 0.42, 0, 1) ** 1.3 - 0.45 * np.clip((y - 0.86) / 0.14, 0, 1)
    im = Image.fromarray((np.asarray(im) * k[..., None]).clip(0, 255).astype(np.uint8)).convert("RGBA")
    words = [w for w in hook.upper().replace("\n", " ").split() if w][:4]; ls = lines_of(words)
    d0 = ImageDraw.Draw(im); fs = [fit(d0, ln, 940) for ln in ls]
    size = min(f.size for f in fs); fs = [F(min(size, 420)) for _ in ls]   # same size on every line, like the long thumbnails
    lh = int(fs[0].size * 0.98); total = lh * len(ls); top = 175
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); sd = ImageDraw.Draw(sh)
    for i, (ln, f) in enumerate(zip(ls, fs)):
        tw = ld.textlength(ln, font=f); L = (W - tw) / 2; ty = top + i * lh
        sd.text((L + 5, ty + 9), ln, font=f, fill=(0, 0, 0, 230), stroke_width=10, stroke_fill=(0, 0, 0, 230))
        ld.text((L, ty), ln, font=f, fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(*AMBER, 255))
    mask = lay.split()[3]; bb = mask.getbbox() or (0, 0, W, H)
    g = np.linspace(0, 1, H)[:, None, None]; top_y, bot_y = bb[1], bb[3]; t = np.clip((np.arange(H)[:, None, None] - top_y) / max(1, bot_y - top_y), 0, 1)
    col = (np.array(CREAM) * (1 - t) + np.array(GOLD) * t).astype(np.uint8); col = np.broadcast_to(col, (H, W, 3))
    fill = Image.fromarray(np.dstack([col, np.asarray(mask)])); fill = Image.composite(fill, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(8)); im = Image.alpha_composite(Image.alpha_composite(im, sh), fill)
    d = ImageDraw.Draw(im); cx = W / 2; ry1, ry2 = max(70, bb[1] - 60), bb[3] + 40
    for yy in (ry1, ry2):   # ornament rules like the long thumbnails: thin gold line with a small diamond in the middle
        d.line((130, yy, cx - 26, yy), fill=GOLD, width=3); d.line((cx + 26, yy, W - 130, yy), fill=GOLD, width=3)
        d.polygon([(cx, yy - 11), (cx + 11, yy), (cx, yy + 11), (cx - 11, yy)], fill=GOLD)
    mf = F(46); t = "BELIEF THROUGH TIME"; tw = d.textlength(t, font=mf)
    d.text(((W - tw) / 2 + 2, 1690 + 3), t, font=mf, fill=(0, 0, 0, 255), stroke_width=4, stroke_fill=(0, 0, 0, 255)); d.text(((W - tw) / 2, 1690), t, font=mf, fill=GOLD)
    im.convert("RGB").save(out, quality=94); cap = fs[0].getbbox("H"); print(f"cap height {(cap[3]-cap[1])/H:.1%} of the image, lines: {len(ls)}")

if __name__ == "__main__":
    cover(sys.argv[1], sys.argv[2], sys.argv[3])
