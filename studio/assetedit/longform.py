"""Long-form (16:9) explainer renderer: approved character sprites + approved backgrounds + infographic cards, cut on the voice.
Usage: python3 longform.py videos/lf01.json        -> renders/<id>.mp4, <id>_thumb.png, <id>_description.txt
Voice is cached in audio/<id>_vo.wav (+ _timing.json); delete it to re-voice."""
import json, math, os, re, subprocess, sys, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.environ.get("KOKORO_DIR", os.path.join(HERE, "..", "voice"))
W, H, FPS = 1920, 1080, 24
INK, CREAM, ORANGE, RED, MUTED = (28, 26, 31), (255, 246, 236), (255, 138, 43), (216, 53, 42), (120, 100, 90)
CH = os.environ.get("CHANNEL_DIR", HERE)  # channel folder with manifest.json, assets/, backgrounds/, shots/
MAN = json.load(open(os.path.join(CH, "manifest.json")))
ASSETS = {a["asset_id"]: a for a in MAN["assets"]}
BGS = {b["bg_id"]: b for b in MAN["backgrounds"]}

def font(sz, w="Bold"):
    for p in (f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > maxw and cur: lines.append(cur); cur = w
        else: cur = t
    return lines + [cur]

def text_block(d, xy, text, f, maxw, fill=INK, gap=1.18, stroke=0, sfill=None, align="left"):
    x, y = xy
    for ln in wrap(d, text, f, maxw):
        lx = x if align == "left" else x + (maxw - d.textlength(ln, font=f)) / 2
        d.text((lx, y), ln, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
        y += f.size * gap
    return y

ease = lambda x: 1 - (1 - min(max(x, 0), 1)) ** 3
def pop(t, n=0.4):  # 0.86 -> 1.06 -> 1.00
    if t >= n: return 1.0
    k = t / n
    return 0.86 + 0.20 * ease(k / 0.6) if k < 0.6 else 1.06 - 0.06 * ease((k - 0.6) / 0.4)

# ---------- validation (strict asset rules) ----------
def validate(v):
    errs = []
    for i, s in enumerate(v["segments"]):
        sh = s["show"]
        if sh.get("type") == "photo":  # free-licensed photo; optional sprite must still be approved
            if not sh.get("file"): errs.append(f"seg {i}: photo without file")
            if sh.get("sprite") and not ASSETS.get(sh["sprite"], {}).get("approved"): errs.append(f"seg {i}: sprite {sh['sprite']} not approved")
            continue
        a = ASSETS.get(sh.get("sprite"))
        if not a or not a.get("approved"): errs.append(f"seg {i}: sprite {sh.get('sprite')} not approved")
        b = BGS.get(sh.get("bg"))
        if not b or not b.get("approved"): errs.append(f"seg {i}: bg {sh.get('bg')} not approved")
        elif a and a["emotion"] not in b["emotions"]: errs.append(f"seg {i}: {sh['sprite']} ({a['emotion']}) not allowed on {sh['bg']}")
        if not s["say"].strip(): errs.append(f"seg {i}: empty voice line")
    if errs: sys.exit("BLOCKED:\n" + "\n".join(errs))

# ---------- voice ----------
def calm_all(v): return v.get("vibe") == "calm"
def voice(v):
    wav, tim = os.path.join(HERE, "audio", v["id"] + "_vo.wav"), os.path.join(HERE, "audio", v["id"] + "_timing.json")
    if os.path.exists(wav) and os.path.exists(tim): return wav, json.load(open(tim))
    sys.path.insert(0, VOICE_DIR); import kokoro_tts as k
    out, timing, t = [], [], 0.0
    for i, s in enumerate(v["segments"]):
        start = t
        calm = v.get("vibe") == "calm"
        # natural flow: speak 1-2 sentences per take (the model carries intonation across them), not one robotic sentence at a time
        sents, chunks = re.split(r"(?<=[.!?])\s+", s["say"].strip()), []
        for sent in sents:
            if chunks and len(chunks[-1]) + len(sent) < 170 and not chunks[-1].endswith("?"): chunks[-1] += " " + sent
            else: chunks.append(sent)
        for ci, sent in enumerate(chunks):
            rng = np.random.default_rng(zlib.crc32(v["id"].encode()) + i * 97 + ci)  # slight, repeatable variation per take
            base = 0.88 if calm else v.get("speed", 1.0)
            a = k.speak(sent, "am_onyx+bm_lewis+bm_lewis" if calm else v.get("voice", "am_puck"), base * float(rng.uniform(0.97, 1.03)))   # 15 Oct owner: calm (Brain After Dark) = "mid D": 1/3 am_onyx + 2/3 bm_lewis, speed 0.88, pitch 0.97, warm EQ
            nz = np.nonzero(np.abs(a) > 0.01)[0]; a = a[max(0, nz[0] - 400):nz[-1] + 900].copy()
            f = int(0.012 * k.SR); a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
            # pause depends on how the take ends: question/colon longer, long take longer, small random jitter
            base_ps = v.get("pause", 0.7 if calm else 0.3)
            ps = base_ps * (1.25 if sent.rstrip().endswith("?") else 1.0) * (1.15 if len(sent) > 110 else 0.9) * float(rng.uniform(0.85, 1.2))
            out += [a, np.zeros(int(ps * k.SR), np.float32)]; t += len(a) / k.SR + ps
        gap = {"chapter": 0.9, "end": 2.0}.get(s["show"]["type"], 0.5)
        out.append(np.zeros(int(gap * k.SR), np.float32)); t += gap
        timing.append({"seg": i, "start": round(start, 3), "end": round(t, 3)})
        print(f"voice {i + 1}/{len(v['segments'])}", flush=True)
    a = np.concatenate(out); a = a / np.abs(a).max() * 0.89
    os.makedirs(os.path.dirname(wav), exist_ok=True); k.save(a, wav)
    if calm_all(v): import flow; flow.warm(wav, 0.97)   # warmer voice for calm (Brain After Dark) videos
    json.dump(timing, open(tim, "w"), indent=1)
    return wav, timing

# ---------- drawing ----------
_bg, _spr = {}, {}
CALM = [False]  # vibe "calm": warm grade, crossfades, no punch/flash/sfx, slower voice (set by the render loop)
_vig = {}
def warm(img):
    """Warm, soft look for calm videos: amber tint + gentle vignette."""
    if "m" not in _vig:
        y, x = np.mgrid[0:H, 0:W]; r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        m = np.clip(1 - 0.32 * np.clip(r - 0.55, 0, 1) ** 1.4, 0, 1)
        _vig["m"] = Image.fromarray((np.dstack([m * 255, m * 238, m * 215])).astype(np.uint8))
    from PIL import ImageChops
    return ImageChops.multiply(img, _vig["m"])
NOW = [0.0]  # global time of the frame being drawn (set by the render loop)
def background(bid, dim):
    """Background slowly drifts (8% larger canvas, slow figure-eight) so no shot is fully still."""
    big = _bgbig(bid, dim); t = NOW[0]
    x = (big.width - W) / 2 * (1 + math.sin(t / 9)); y = (big.height - H) / 2 * (1 + math.sin(t / 13 + 1))
    return big.crop((round(x), round(y), round(x) + W, round(y) + H))

def _bgbig(bid, dim):
    key = (bid, dim)
    if key not in _bg:
        im = Image.open(os.path.join(CH, BGS[bid]["file_path"])).convert("RGB").resize((round(W * 1.08), round(H * 1.08)), Image.LANCZOS)
        if dim:
            im = im.filter(ImageFilter.GaussianBlur(6))
            im = Image.blend(im, Image.new("RGB", im.size, (20, 16, 24)), 0.45)
        _bg[key] = im
    return _bg[key]

_src = {}
def sprite(aid, scale):
    """Uses the 4x upscaled sprite (assets_hd/, same art, sharper) when it exists."""
    key = (aid, round(scale, 2))
    if key not in _spr:
        if aid not in _src:
            hd = os.path.join(CH, "assets_hd", os.path.basename(ASSETS[aid]["file_path"]))
            _src[aid] = (Image.open(hd).convert("RGBA"), 4) if os.path.exists(hd) else (Image.open(os.path.join(CH, ASSETS[aid]["file_path"])).convert("RGBA"), 1)
        im, k = _src[aid]
        if len(_spr) > 120: _spr.clear()  # long videos: keep memory bounded
        _spr[key] = im.resize((round(im.width * scale / k), round(im.height * scale / k)), Image.LANCZOS)  # uniform scale only
    return _spr[key]

def place_sprite(img, aid, cx, base_scale, lt):
    """Pop in, then idle: slow breathing + bob so the character never looks frozen."""
    sp_ = 1.3 if CALM[0] else 2.2
    br = 1 + 0.012 * math.sin(lt * sp_) if (lt > 0.4 or CALM[0]) else 1
    sp = sprite(aid, base_scale * (1 if CALM[0] else pop(lt)) * br)
    img.paste(sp, (round(cx - sp.width / 2 + 6 * math.sin(lt * 0.6)), round(H - sp.height + 10 + 7 * math.sin(lt * sp_ + 1))), sp)

def panel(d, box, fill=CREAM):
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0 + 10, y0 + 14, x1 + 10, y1 + 14), 34, fill=(12, 10, 14))
    d.rounded_rectangle(box, 34, fill=fill, outline=INK, width=6)

def card_static(d, sh, oy):
    """Everything on the card that does not animate. oy = slide offset."""
    t, X0, Y0, X1, Y1 = sh["type"], 110, 110 + oy, 1300, 900 + oy
    if t == "chapter":
        d.text((140, 330 + oy), f"PART {sh['n']}", font=font(64, "Black"), fill=ORANGE, stroke_width=8, stroke_fill=INK)
        text_block(d, (140, 420 + oy), sh["title"], font(118, "Black"), 1150, fill=CREAM, gap=1.08, stroke=10, sfill=INK)
        return
    if t == "char":
        if sh.get("cap"): text_block(d, (120, 380 + oy), sh["cap"], font(104, "Black"), 900, fill=CREAM, gap=1.08, stroke=10, sfill=INK)
        if sh.get("sub"): text_block(d, (124, 760 + oy), sh["sub"], font(46, "SemiBold"), 860, fill=CREAM, stroke=6, sfill=INK)
        return
    if t == "end":
        d.text((140, 250 + oy), "NEXT UP", font=font(64, "Black"), fill=ORANGE, stroke_width=8, stroke_fill=INK)
        text_block(d, (140, 340 + oy), sh["next"], font(92, "Black"), 1150, fill=CREAM, gap=1.08, stroke=10, sfill=INK)
        return
    panel(d, (X0, Y0, X1, Y1))
    if sh.get("title"): text_block(d, (X0 + 70, Y0 + 60), sh["title"], font(60, "Black"), X1 - X0 - 140)
    if t == "quote":
        d.text((X0 + 60, Y0 + 20), "\u201c", font=font(220, "Black"), fill=ORANGE)
        y = text_block(d, (X0 + 90, Y0 + 230), sh["text"], font(66, "Bold"), X1 - X0 - 180, gap=1.2)
        d.text((X0 + 90, y + 30), "\u2014 " + sh["by"], font=font(44, "SemiBold"), fill=MUTED)
    if t == "study":
        d.rounded_rectangle((X0 + 70, Y0 + 60, X0 + 470, Y0 + 130), 20, fill=INK)
        d.text((X0 + 98, Y0 + 72), "THE STUDY", font=font(44, "Black"), fill=CREAM)
        y = text_block(d, (X0 + 70, Y0 + 180), sh["who"], font(56, "Black"), X1 - X0 - 140)
        y = text_block(d, (X0 + 70, y + 6), sh["where"], font(42, "SemiBold"), X1 - X0 - 140, fill=MUTED)  # wrap: long "where" lines ran off the card (lf10)
        text_block(d, (X0 + 70, y + 34), sh["what"], font(48, "Medium"), X1 - X0 - 140, gap=1.3)
    if t == "curve":
        ax0, ay0, ax1, ay1 = X0 + 130, Y0 + 210, X1 - 90, Y1 - 120
        d.line((ax0, ay1, ax1, ay1), fill=INK, width=6); d.line((ax0, ay0, ax0, ay1), fill=INK, width=6)
        d.text(((ax0 + ax1) / 2 - 80, ay1 + 26), sh["x"], font=font(44, "Bold"), fill=INK)
        d.text((X0 + 40, ay0 - 70), sh["y"], font=font(44, "Bold"), fill=INK)

def card_dynamic(d, sh, lt, dur):
    """Animated parts: list reveals, growing bars, counting stats, the curve drawing."""
    t, X0, Y0, X1, Y1 = sh["type"], 110, 110, 1300, 900
    if t == "list":
        n, maxw = len(sh["items"]), X1 - X0 - 260
        top = Y0 + 60 + len(wrap(d, sh.get("title", ""), font(60, "Black"), X1 - X0 - 140)) * 71 + 40
        for sz in (64, 56, 48):  # shrink until the whole list fits in the card
            f = font(sz, "Bold"); hs = [len(wrap(d, it, f, maxw)) * round(sz * 1.19) for it in sh["items"]]
            if sum(hs) + 50 * (n - 1) <= Y1 - 60 - top: break
        y = top + max(0, (Y1 - 60 - top - sum(hs) - 50 * (n - 1)) / 2)  # centre the full list, so reveals don't shift it
        for i, it in enumerate(sh["items"]):
            if lt < 0.3 + i * max(0.6, (dur * 0.7) / n): break
            d.ellipse((X0 + 70, y + 6, X0 + 136, y + 72), fill=ORANGE, outline=INK, width=5)
            d.text((X0 + 103 - d.textlength(str(i + 1), font=font(44, "Black")) / 2, y + 12), str(i + 1), font=font(44, "Black"), fill=INK)
            text_block(d, (X0 + 170, y), it, f, maxw, gap=1.19)
            y += hs[i] + 50
    if t == "stat":
        k = ease((lt - 0.2) / 0.9); m = re.match(r"([^\d]*)([\d.,]+)(.*)", sh["big"])
        big = sh["big"] if not m else f"{m.group(1)}{round(float(m.group(2).replace(',', '')) * k):,}{m.group(3)}"
        f = font(260, "Black"); tw = d.textlength(big, font=f)
        d.text((X0 + (X1 - X0 - tw) / 2, Y0 + 170), big, font=f, fill=ORANGE, stroke_width=10, stroke_fill=INK)
        text_block(d, (X0 + 80, Y0 + 520), sh["label"], font(64, "Bold"), X1 - X0 - 160, align="center")
    if t == "bars":
        n = len(sh["bars"]); top = max(b[1] for b in sh["bars"]); k = ease((lt - 0.3) / 1.0)
        bw = (X1 - X0 - 200) / n; base = Y1 - 150
        for i, (lab, val) in enumerate(sh["bars"]):
            x = X0 + 100 + i * bw; hgt = (base - Y0 - 280) * val / top * k
            d.rectangle((x + 30, base - hgt, x + bw - 30, base), fill=ORANGE if i % 2 == 0 else RED, outline=INK, width=6)
            num = f"{round(val * k)}{sh.get('unit', '')}"; f = font(76, "Black")
            d.text((x + (bw - d.textlength(num, font=f)) / 2, base - hgt - 96), num, font=f, fill=INK)
            text_block(d, (x + 10, base + 20), lab, font(40, "Bold"), bw - 20, align="center")
    if t == "curve":
        ax0, ay0, ax1, ay1 = X0 + 130, Y0 + 210, X1 - 90, Y1 - 120
        k = ease((lt - 0.2) / 1.4); pk = sh.get("peak", 0.5); pts = []
        for i in range(int(120 * k) + 1):
            u = i / 120; v = math.exp(-((u - pk) ** 2) / 0.06)
            pts.append((ax0 + 20 + u * (ax1 - ax0 - 40), ay1 - 20 - v * (ay1 - ay0 - 60)))
        if len(pts) > 1: d.line(pts, fill=ORANGE, width=14, joint="curve")
        if lt > 1.8:
            px, py = ax0 + 20 + pk * (ax1 - ax0 - 40), ay0 + 40
            d.ellipse((px - 22, py - 22, px + 22, py + 22), fill=RED, outline=INK, width=5)
            f = font(48, "Black"); d.text((px - d.textlength(sh["label"], font=f) / 2, py - 92), sh["label"], font=f, fill=INK)

_shot = {}
def screen(img, sh, lt, dur):
    """Screenshot (shots/<file>) in a browser frame. Per-scene motion keeps every video different:
    move = zoom | scroll | pan; focus = [x, y] (0-1) of the part to end on; side = left | right."""
    if sh["file"] not in _shot: _shot[sh["file"]] = Image.open(os.path.join(CH, "shots", sh["file"])).convert("RGB")
    s = _shot[sh["file"]]; k = ease(lt / max(dur, .1)); fx, fy = sh.get("focus", [.5, .3]); mv = sh.get("move", "zoom")
    fw, fh = 1180, 760; z = 1 + (.55 * k if mv == "zoom" else .25)
    cw, chh = s.width / z, s.width / z * fh / fw
    cx = (s.width - cw) * (fx if mv != "pan" else k * fx); cy = max(0, min(s.height - chh, (s.height - chh) * (fy if mv != "scroll" else k * fy)))
    view = s.resize((fw, fh), Image.LANCZOS, box=(cx, cy, cx + cw, cy + chh))
    x0 = 110 if sh.get("side", "left") == "left" else W - 110 - fw; y0 = 150
    d = ImageDraw.Draw(img); d.rounded_rectangle((x0 + 12, y0 + 16, x0 + fw + 12, y0 + fh + 76), 24, fill=(10, 10, 14))
    d.rounded_rectangle((x0, y0, x0 + fw, y0 + fh + 60), 24, fill=(236, 238, 243), outline=INK, width=5)
    for i, c in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))): d.ellipse((x0 + 24 + i * 34, y0 + 20, x0 + 46 + i * 34, y0 + 42), fill=c)
    d.rounded_rectangle((x0 + 140, y0 + 14, x0 + fw - 30, y0 + 48), 17, fill=(255, 255, 255))
    d.text((x0 + 160, y0 + 19), sh.get("url", "")[:70], font=font(22, "Medium"), fill=MUTED)
    img.paste(view, (x0, y0 + 60))
    if sh.get("cap"): text_block(d, (x0, y0 + fh + 90), sh["cap"], font(50, "Black"), fw, fill=CREAM, stroke=8, sfill=INK)

def photo(sh, lt, dur):
    """Free-licensed photo (photos/<file>) full screen with a slow Ken Burns move; credit line bottom-left."""
    if sh["file"] not in _shot: _shot[sh["file"]] = Image.open(os.path.join(CH, "photos", sh["file"])).convert("RGB")
    s = _shot[sh["file"]]; k = ease(lt / max(dur, .1)); z0, z1 = (1.0, 1.15) if sh.get("move", "in") == "in" else (1.15, 1.0)
    z = z0 + (z1 - z0) * k; base = max(W / s.width, H / s.height); cw, chh = W / (base * z), H / (base * z)
    fx, fy = sh.get("focus", [.5, .5]); cx = (s.width - cw) * fx; cy = (s.height - chh) * fy
    img = s.resize((W, H), Image.LANCZOS, box=(cx, cy, cx + cw, cy + chh))
    vg = Image.new("L", (W, H), 0); ImageDraw.Draw(vg).rectangle((0, H - 320, W, H), fill=150); img.paste((10, 10, 14), (0, 0), vg.filter(ImageFilter.GaussianBlur(120)))
    d = ImageDraw.Draw(img)
    if sh.get("cap"): text_block(d, (110, H - 250), sh["cap"], font(64, "Black"), 1150, fill=CREAM, stroke=9, sfill=INK)
    cr = json.load(open(os.path.join(CH, "photos", "credits.json"))).get(sh["file"], {})
    d.text((24, H - 40), "AI-generated image" if cr.get("ai") else f'Photo: {cr.get("creator") or "unknown"} / {cr.get("provider", "")} ({cr.get("license", "")})', font=font(22, "Medium"), fill=(235, 235, 235))
    return img

def frame_for(seg, lt, dur, beat=0):
    sh = seg["show"]; t = sh["type"]
    if CALM[0] and t == "chapter":
        seg = dict(seg, show=dict(sh, type="char", cap=sh["title"], sub=None)); sh = seg["show"]; t = "char"
    if t == "photo":
        img = photo(sh, lt, dur)
        if sh.get("sprite"): place_sprite(img, sh["sprite"], 1650, 1.8, lt)
        return finish(img, seg, lt, 1.0)
    if t == "screen":
        img = background(sh["bg"], dim=True).copy(); screen(img, sh, lt, dur)
        place_sprite(img, sh["sprite"], 1640 if sh.get("side", "left") == "left" else 280, 2.0, lt); return finish(img, seg, lt, 1.0)
    fullscreen = t in ("char", "chapter", "end")
    img = background(sh["bg"], dim=not fullscreen or t != "char").copy()
    d = ImageDraw.Draw(img)
    oy = round((1 - ease(lt / (0.8 if CALM[0] else 0.3))) * (30 if CALM[0] else 60))
    card_static(d, sh, oy)
    if oy == 0: card_dynamic(d, sh, lt, dur)
    if t == "char": place_sprite(img, sh["sprite"], 1420, 3.1, lt)
    elif t in ("chapter", "end"): place_sprite(img, sh["sprite"], 1560, 2.6, lt)
    else: place_sprite(img, sh["sprite"], 1620, 2.0, lt)
    z, shift = 1.0, (0, 0)
    if t == "char" and CALM[0]:  # re-frame on every sentence (wide -> toward the text -> close on the character) so one scene never sits still
        k = beat % 3; z = (1.0, 1.07, 1.13)[k] + 0.03 * min(lt / max(dur, 0.1), 1); shift = ((0, 0), (-170, 10), (210, 30))[k]
    elif t == "char": z = 1.0 + 0.025 * min(lt / max(dur, 0.1), 1) + (0.07 if beat % 2 else 0)  # slow push-in keeps static shots alive
    return finish(img, seg, lt, z, shift)

def finish(img, seg, lt, z=1.0, shift=(0, 0)):
    """Motion-graphics layer on every frame: punch-in transition on each new scene, white flash on chapters,
    and a progress bar for the current part (seg['_p'] = [n, title, start, end], set by the render loop)."""
    if CALM[0]:
        if z > 1.001:
            cw, ch = W / z, H / z; dx = max(-(W - cw) / 2, min((W - cw) / 2, shift[0])); dy = max(-(H - ch) / 2, min((H - ch) / 2, shift[1]))
            img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2 + dx, (H - ch) / 2 + dy, (W + cw) / 2 + dx, (H + ch) / 2 + dy))
        return warm(img)
    if lt < 0.22: z *= 1 + 0.06 * (1 - ease(lt / 0.22))
    if z > 1.001:
        cw, ch = W / z, H / z
        img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    if seg["show"]["type"] == "chapter" and lt < 0.18: img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.7 * (1 - lt / 0.18))
    p = seg.get("_p")
    if p and seg["show"]["type"] not in ("chapter", "end"):
        d = ImageDraw.Draw(img); k = min(max((NOW[0] - p[2]) / max(p[3] - p[2], 1), 0), 1)
        d.rounded_rectangle((40, 30, 520, 44), 7, fill=(20, 16, 24)); d.rounded_rectangle((40, 30, 40 + max(14, 480 * k), 44), 7, fill=ORANGE)
        d.text((40, 52), f"PART {p[0]}  \u00b7  {p[1]}"[:48], font=font(26, "Bold"), fill=CREAM, stroke_width=4, stroke_fill=INK)
    return img

def music(total, timing, v, path, sr=24000):
    t = np.arange(int(total * sr)) / sr; out = np.zeros_like(t)
    chords = [(261.6, 329.6, 392.0), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7)]
    for i, ch in enumerate(chords * int(total / 27.4 + 2)):
        a, b = int(i * 6.86 * sr), int((i + 1) * 6.86 * sr)
        if a >= len(t): break
        seg = t[a:b] - t[a]; env = np.minimum(1, seg / 1.5) * np.minimum(1, (6.86 - seg) / 1.5)
        out[a:b] += env * sum(np.sin(2 * np.pi * f / 2 * seg) + 0.3 * np.sin(2 * np.pi * f * seg) for f in ch)
    for s, tm in zip(v["segments"], timing):  # silence the bed around chapter cards = "drop before the reveal"
        if s["show"]["type"] == "chapter" and v.get("vibe") != "calm":
            a, b = int((tm["start"] - 0.8) * sr), int((tm["end"] + 0.6) * sr); out[max(a, 0):b] *= 0.0
    out = np.convolve(out, np.ones(60) / 60, "same")  # soften
    out = out / np.sqrt((out ** 2).mean() + 1e-9) * 10 ** ((-43 if v.get("vibe") == "calm" else -40) / 20)  # ~24 dB under the -16 LUFS voice
    sys.path.insert(0, VOICE_DIR); import kokoro_tts as k; k.save(out.astype(np.float32), path)
    return path

# ---------- outputs ----------
ACCENTS = [(255, 176, 59), (255, 105, 160), (64, 214, 255), (150, 235, 80), (176, 120, 255), (255, 92, 92), (40, 225, 180), (255, 225, 60), (255, 140, 60), (110, 150, 255)]
def thumbnail(v, path):
    # MrBeast-style: 1 face big ("rule of big"), <=3 words that add to the title, simple saturated cool background,
    # rim-lit subject, white/yellow text with thick black stroke + hard shadow, top-left text, bottom-right corner free.
    from PIL import ImageFilter, ImageEnhance, ImageChops
    th = v["thumb"]; img = Image.open(os.path.join(CH, BGS[th["bg"]]["file_path"])).convert("RGB").resize((1280, 720), Image.LANCZOS)
    img = ImageEnhance.Color(img.filter(ImageFilter.GaussianBlur(7))).enhance(1.6)
    calm = v.get("vibe") == "calm"  # calm videos: warm night grade, amber rim, last word on a warm block (trend: text left + one word on a colour block)
    mir = th.get("mirror"); acc = tuple(int(th["accent"][i:i + 2], 16) for i in (1, 3, 5)) if th.get("accent") and th.get("accent_lock") else ACCENTS[int(re.sub(r"\D", "", v["id"]) or 0) % len(ACCENTS)]   # 15 Oct owner: every thumbnail its own colour (rim glow + word block)  # variety: text right/sprite left, own block + rim colour
    img = Image.blend(img, Image.new("RGB", img.size, (255, 140, 50) if calm else (24, 110, 190)), 0.22 if calm else 0.28)
    yy, xx = np.mgrid[0:720, 0:1280]; vig = 1 - 0.45 * (((xx - 900) / 900) ** 2 + ((yy - 360) / 520) ** 2).clip(0, 1)
    img = Image.fromarray((np.asarray(img) * vig[..., None]).astype(np.uint8))
    if mir: img = img.transpose(Image.FLIP_LEFT_RIGHT)  # mirror only the background: sprites carry symbols ("?") that must not flip
    hd = os.path.join(CH, "assets_hd", os.path.basename(ASSETS[th["sprite"]]["file_path"])); k = 4 if os.path.exists(hd) else 1  # sharp 4x sprite when available
    sp = Image.open(hd if k == 4 else os.path.join(CH, ASSETS[th["sprite"]]["file_path"])).convert("RGBA")
    sp = ImageEnhance.Color(sp.resize((round(sp.width * 3.15 / k), round(sp.height * 3.15 / k)), Image.LANCZOS)).enhance(1.25)
    # sprites are cropped at their image border: fade those cut edges so no straight lines show
    al = np.asarray(sp.split()[-1]).astype(float); h, w = al.shape; F = 60; ramp = np.linspace(0, 1, F)
    if al[:, 0].max() > 0: al[:, :F] *= ramp[None, :]
    if al[0, :].max() > 0: al[:F, :] *= ramp[:, None]
    if al[:, -1].max() > 0: al[:, -F:] *= ramp[::-1][None, :]
    P = 40; a = Image.new("L", (w + 2 * P, h + 2 * P)); a.paste(Image.fromarray(al.astype(np.uint8)), (P, P))
    sp.putalpha(Image.fromarray(al.astype(np.uint8))); x0, y0 = (10 if mir else 1280 - w - 10), 720 - h + 150
    for grow, col in ((22, (acc if th.get("accent") else (255, 186, 80)) if calm else (0, 230, 255)), (10, (255, 255, 255))):  # rim light, then white sticker edge
        rim = Image.new("RGBA", a.size, col + (0,)); rim.putalpha(a.point(lambda p: 255 if p > 128 else 0).filter(ImageFilter.MaxFilter(grow * 2 + 1)))
        if grow > 12: rim = rim.filter(ImageFilter.GaussianBlur(6))
        img.paste(rim, (x0 - P, y0 - P), rim)
    img.paste(sp, (x0, y0), sp)
    d = ImageDraw.Draw(img); y = 60; lines = th["text"].split("|")
    for i, ln in enumerate(lines):
        f = font(150 if len(ln) <= 7 else 124, "Black"); last = i == len(lines) - 1; fill = (255, 230, 0) if last else (255, 255, 255)
        tw = d.textlength(ln, font=f); L = 1280 - 150 - tw if mir else 50  # left edge of the line (right-aligned when mirrored)
        if calm and last and len(lines) > 1:  # warm block behind the last word
            d.rounded_rectangle((L + 12, y + 34, L + 12 + tw + 56, y + f.size * 1.02 + 34), 22, fill=(0, 0, 0))
            d.rounded_rectangle((L, y + 22, L + tw + 56, y + f.size * 1.02 + 22), 22, fill=acc, outline=(0, 0, 0), width=8)
            d.text((L + 28, y), ln, font=f, fill=(28, 20, 14)); y += f.size * 1.12; continue
        d.text((L + 12, y + 10), ln, font=f, fill=(0, 0, 0), stroke_width=16, stroke_fill=(0, 0, 0))  # hard drop shadow
        d.text((L, y), ln, font=f, fill=fill, stroke_width=16, stroke_fill=(0, 0, 0)); y += f.size * 1.05
    img.save(path, quality=95)

def description(v, timing, series, path):
    def ts(s): s = int(s); return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"
    chap = [("0:00", "Intro")] + [(ts(timing[i]["start"]), s["show"]["title"]) for i, s in enumerate(v["segments"]) if s["show"]["type"] == "chapter"]
    idx = [x["id"] for x in series].index(v["id"])
    nxt = series[idx + 1:idx + 4]
    lines = [v["desc"]] + (["", "\u23f1 Chapters"] + [f"{a} {b}" for a, b in chap] if v.get("vibe") != "calm" else []) + (["", "\U0001f52e Coming up next on the channel:"] if nxt else [])  # no empty header when nothing is planned
    lines += [f"\u25b8 {x['title']}" for x in nxt] + ["", "\U0001f4da Sources"] + [f"\u2022 {s}" for s in v["sources"]]
    cpath = os.path.join(CH, "photos", "credits.json"); used = [s["show"]["file"] for s in v["segments"] if s["show"]["type"] == "photo"]
    if used and os.path.exists(cpath):
        cr = json.load(open(cpath)); real = [f for f in dict.fromkeys(used) if f in cr and not cr[f].get("ai")]
        pd = [f for f in real if cr[f]["license"].split()[0] in ("CC0", "PDM")]  # public domain: no attribution required
        credit = [f'\u2022 "{cr[f]["title"][:28].rstrip()}" by {cr[f]["creator"]}, {cr[f]["license"]}: {cr[f]["source"]}' for f in real if f not in pd]
        lines += ["", "\U0001f4f7 Photos"] + credit + (["\u2022 Other photos: public domain (CC0 / PDM)."] if pd else [])
        if any(cr.get(f, {}).get("ai") for f in used): lines += ["\u2022 Some images are AI-generated (Flux)."]
    lines += ["", "Narration is AI-generated (synthetic voice). Script, research and edit by the channel.", "", " ".join(v["tags"])]
    keep = set(credit) if used and os.path.exists(cpath) else set()  # photo credits keep author, license and link (CC BY rule)
    for cut in (100, 75, 55, 40, 30):  # YouTube description limit is 5000 characters: shorten source lines step by step
        if len("\n".join(lines)) <= 4900: break
        lines = [l[:cut - 3].rstrip(" ,;:") + "\u2026" if l.startswith("\u2022 ") and l not in keep and len(l) > cut else l for l in lines]
    open(path, "w").write("\n".join(lines) + "\n")

if __name__ == "__main__":
    v = json.load(open(sys.argv[1])); validate(v)
    series = json.load(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "series.json"))) if not v.get("part") else []
    wav, timing = voice(v)
    total = timing[-1]["end"]; N = round(total * FPS)
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    out = os.path.join(HERE, "renders", v["id"] + ".mp4"); silent = out[:-4] + "_silent.mp4"
    # parts (for the progress bar) + word-by-word captions (same green pop-up style as the Shorts)
    cur = None
    for s_, tm in zip(v["segments"], timing):
        if s_["show"]["type"] == "chapter": cur = [s_["show"]["n"], s_["show"]["title"], tm["start"], None]
        if cur: s_["_p"] = cur
    ends = {}
    for s_, tm in zip(v["segments"], timing):
        if s_.get("_p"): ends[id(s_["_p"])] = tm["end"]
    for s_ in v["segments"]:
        if s_.get("_p"): s_["_p"][3] = ends[id(s_["_p"])]
    vf = []
    if v.get("captions", True):
        from shorts import captions, sentence_spans
        cap = out[:-4] + ".ass"; captions(v["segments"], timing, 0, total, cap, res=(W, H), size=56 if v.get("vibe") == "calm" else 60, outline=6 if v.get("vibe") == "calm" else 7,
                                          marginv=40, ml=90, mr=760, calm=v.get("vibe") == "calm", spans=sentence_spans(wav, v["segments"], timing)); vf = ["-vf", "ass=" + cap]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *vf,
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    import wave
    w = wave.open(wav); va = np.abs(np.frombuffer(w.readframes(w.getnframes()), np.int16)); sr = w.getframerate()
    quiet = np.convolve(va > 300, np.ones(int(0.3 * sr)), "valid") == 0  # 0.3 s of silence = sentence gap
    beats = np.flatnonzero(np.diff(quiet.astype(int)) == -1) / sr + 0.3
    si = 0
    CALM[0] = v.get("vibe") == "calm"; prev, last_si = None, -1
    for f in range(N):
        t = f / FPS; NOW[0] = t
        while si + 1 < len(timing) and t >= timing[si + 1]["start"]: si += 1
        seg, tm = v["segments"][si], timing[si]
        fr = frame_for(seg, t - tm["start"], tm["end"] - tm["start"], int(((beats > tm["start"] + 0.2) & (beats <= t)).sum()))
        if CALM[0]:  # 0.7 s crossfade from the last frame of the previous scene
            if si != last_si: hold, last_si = prev, si
            if hold is not None and t - tm["start"] < 0.7: fr = Image.blend(hold, fr, ease((t - tm["start"]) / 0.7))
            prev = fr
        ff.stdin.write(fr.tobytes())
        if f % (FPS * 30) == 0: print(f"video {t / total:5.1%}", flush=True)
    ff.stdin.close(); ff.wait()
    # sfx: soft whoosh on every card/chapter, pop on character scenes
    sfx = os.path.join(HERE, "..", "remotion", "public", "sfx"); ins, flt, lab = ["-i", wav], ["[1]loudnorm=I=-16:TP=-1.5[v]"], ["[v]"]
    for i, (s, tm) in enumerate(zip(v["segments"], timing)):
        if i == 0 or CALM[0]: continue
        ins += ["-i", os.path.join(sfx, {"char": "pop.wav", "stat": "boom.wav", "bars": "boom.wav"}.get(s["show"]["type"], "whoosh.wav"))]
        ms = round(tm["start"] * 1000); flt.append(f"[{len(lab) + 1}]adelay={ms}|{ms},volume=0.22[s{i}]"); lab.append(f"[s{i}]")
    ins += ["-i", music(total, timing, v, out[:-4] + "_music.wav")]; flt.append(f"[{len(lab) + 1}]anull[mu]"); lab.append("[mu]")
    flt.append("".join(lab) + f"amix=inputs={len(lab)}:normalize=0[m]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, *ins, "-filter_complex", ";".join(flt), "-map", "0:v", "-map", "[m]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", out], check=True)
    os.remove(silent); os.remove(out[:-4] + "_music.wav")
    if os.path.exists(out[:-4] + ".ass"): os.remove(out[:-4] + ".ass")
    if not v.get("part"):  # parts of a 2.5 h video get their thumbnail/description from mega.py
        thumbnail(v, out[:-4] + "_thumb.png"); description(v, timing, series, out[:-4] + "_description.txt")
    print(f"DONE {out} {total / 60:.2f} min")
