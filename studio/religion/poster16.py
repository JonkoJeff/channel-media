"""Belief Through Time long-video thumbnail for the portrait POSTER art (bible_01..10: a ~4:5 poster centred on blurred side bars, so it showed as a small
strip on a phone). Poster is cut out, sits on one side (left/right alternates per episode) with a gold rim, the rest is the same art blown up, blurred and
warm-graded, and a big hook (different words than the poster's own title) fills the other side. 16:9 art (Quran, Hinduism, Christianity) is returned unchanged (None).
heads: studio/channels/religion/thumb_heads.json {"02": "THE FIRST|HUMANS"}"""
import json, os, re, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"; HEADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "channels", "religion", "thumb_heads.json")
ACC = [(232, 195, 106), (255, 150, 80), (127, 227, 216), (244, 140, 170), (242, 230, 201)]

def poster_box(im):
    """The posters are ~700x720 centred on blurred side bars (x 290..990 of 1280). 16:9 art has sharp edges: return None."""
    if im.size != (1280, 720): im = im.resize((1280, 720))
    g = np.asarray(im.convert("L")).astype(float); s = np.abs(np.diff(g, axis=1)).mean(0)
    out = (s[:240].mean() + s[1040:].mean()) / 2; inner = s[330:950].mean()
    return (312, 0, 968, 720) if out < 0.6 * inner else None

def make(art, n, out, head=None):
    im = Image.open(art).convert("RGB"); box = poster_box(im)
    if not box: return None
    ep = int(re.sub(r"\D", "", str(n)) or 0); poster = im.crop(box); acc = ACC[ep % len(ACC)]; left = ep % 2 == 0   # poster side
    W, H = 1280, 720; r = max(W / im.width, H / im.height)
    bg = im.crop(box).resize((W, round(W * poster.height / poster.width)), Image.LANCZOS); bg = bg.crop((0, (bg.height - H) // 2, W, (bg.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(14))
    bg = ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(1.4)).enhance(0.55)
    x = np.linspace(0, 1, W)[None, :]; k = 0.55 + 0.45 * (x if left else 1 - x)   # darker behind the poster side, glow behind the text
    bg = Image.fromarray((np.asarray(bg) * k[..., None]).clip(0, 255).astype(np.uint8))
    ph = round(H * 0.9); pw = round(poster.width * ph / poster.height); p = poster.resize((pw, ph), Image.LANCZOS)
    px = 44 if left else W - pw - 44; py = (H - ph) // 2
    a = Image.new("L", (W, H)); a.paste(255, (px - 6, py - 6, px + pw + 6, py + ph + 6)); rim = Image.new("RGB", (W, H), acc)
    bg.paste(rim, (0, 0), a.filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(10))); bg.paste(p, (px, py)); d = ImageDraw.Draw(bg)
    heads = json.load(open(HEADS)) if os.path.exists(HEADS) else {}; txt = head or heads.get(f"{ep:02d}") or heads.get(str(ep)) or ""
    toks = txt.upper().replace("|", " ").split(); lines = []; carry = ""
    for t in toks:   # one word per line (biggest type); 1-2 letter words (A, OF, BY) stay with the next word
        carry = (carry + " " + t).strip()
        if len(t) > 2: lines.append(carry); carry = ""
    if carry: lines.append(carry)
    if lines:
        SQ = 0.80; x0 = (px + pw + 50) if left else 40; avail = W - pw - 44 - 50 - 40 - 10; size = 190   # type is squeezed 20 % wide so it can be taller
        while size > 60 and max(d.textlength(l, font=ImageFont.truetype(SERIF, size)) for l in lines) * SQ > avail: size -= 4
        f = ImageFont.truetype(SERIF, size); step = int(size * 1.08); y = (H - step * len(lines)) // 2
        for i, ln in enumerate(lines):
            tw = int(d.textlength(ln, font=f)); lay = Image.new("RGBA", (tw + 80, step + 60), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); ox, oy = 40, 24
            if i == len(lines) - 1 and len(lines) > 1:
                ld.rounded_rectangle((ox - 22 + 10, oy + 14 + 10, ox + tw + 22 + 10, oy + step + 10), 22, fill=(0, 0, 0, 255)); ld.rounded_rectangle((ox - 22, oy + 14, ox + tw + 22, oy + step), 22, fill=acc + (255,), outline=(0, 0, 0, 255), width=6)
                ld.text((ox, oy), ln, font=f, fill=(24, 18, 12, 255))
            else:
                ld.text((ox + 7, oy + 7), ln, font=f, fill=(0, 0, 0, 255), stroke_width=12, stroke_fill=(0, 0, 0, 255)); ld.text((ox, oy), ln, font=f, fill=(255, 255, 255, 255), stroke_width=12, stroke_fill=(0, 0, 0, 255))
            lay = lay.resize((round(lay.width * SQ), lay.height), Image.LANCZOS); bg.paste(lay, (x0 - round(40 * SQ), y - 24), lay); y += step
    bg.save(out, quality=94); return out

if __name__ == "__main__":
    import sys; print(make(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None))
