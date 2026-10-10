"""Long-form (16:9) explainer renderer: approved character sprites + approved backgrounds + infographic cards, cut on the voice.
Usage: python3 longform.py videos/lf01.json        -> renders/<id>.mp4, <id>_thumb.png, <id>_description.txt
Voice is cached in audio/<id>_vo.wav (+ _timing.json); delete it to re-voice."""
import json, math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.environ.get("KOKORO_DIR", os.path.join(HERE, "..", "voice"))
W, H, FPS = 1920, 1080, 24
INK, CREAM, ORANGE, RED, MUTED = (28, 26, 31), (255, 246, 236), (255, 138, 43), (216, 53, 42), (120, 100, 90)
MAN = json.load(open(os.path.join(HERE, "manifest.json")))
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
        sh = s["show"]; a = ASSETS.get(sh.get("sprite"))
        if not a or not a.get("approved"): errs.append(f"seg {i}: sprite {sh.get('sprite')} not approved")
        b = BGS.get(sh.get("bg"))
        if not b or not b.get("approved"): errs.append(f"seg {i}: bg {sh.get('bg')} not approved")
        elif a and a["emotion"] not in b["emotions"]: errs.append(f"seg {i}: {sh['sprite']} ({a['emotion']}) not allowed on {sh['bg']}")
        if not s["say"].strip(): errs.append(f"seg {i}: empty voice line")
    if errs: sys.exit("BLOCKED:\n" + "\n".join(errs))

# ---------- voice ----------
def voice(v):
    wav, tim = os.path.join(HERE, "audio", v["id"] + "_vo.wav"), os.path.join(HERE, "audio", v["id"] + "_timing.json")
    if os.path.exists(wav) and os.path.exists(tim): return wav, json.load(open(tim))
    sys.path.insert(0, VOICE_DIR); import kokoro_tts as k
    out, timing, t = [], [], 0.0
    for i, s in enumerate(v["segments"]):
        start = t
        for sent in re.split(r"(?<=[.!?])\s+", s["say"].strip()):
            a = k.speak(sent, v.get("voice", "am_puck"), 1.0)
            nz = np.nonzero(np.abs(a) > 0.01)[0]; a = a[max(0, nz[0] - 600):nz[-1] + 1200]
            out += [a, np.zeros(int(0.4 * k.SR), np.float32)]; t += len(a) / k.SR + 0.4
        gap = {"chapter": 0.9, "end": 2.0}.get(s["show"]["type"], 0.5)
        out.append(np.zeros(int(gap * k.SR), np.float32)); t += gap
        timing.append({"seg": i, "start": round(start, 3), "end": round(t, 3)})
        print(f"voice {i + 1}/{len(v['segments'])}", flush=True)
    a = np.concatenate(out); a = a / np.abs(a).max() * 0.89
    os.makedirs(os.path.dirname(wav), exist_ok=True); k.save(a, wav); json.dump(timing, open(tim, "w"), indent=1)
    return wav, timing

# ---------- drawing ----------
_bg, _spr = {}, {}
def background(bid, dim):
    key = (bid, dim)
    if key not in _bg:
        im = Image.open(os.path.join(HERE, BGS[bid]["file_path"])).convert("RGB").resize((W, H), Image.LANCZOS)
        if dim:
            im = im.filter(ImageFilter.GaussianBlur(6))
            im = Image.blend(im, Image.new("RGB", (W, H), (20, 16, 24)), 0.45)
        _bg[key] = im
    return _bg[key]

def sprite(aid, scale):
    key = (aid, round(scale, 3))
    if key not in _spr:
        im = Image.open(os.path.join(HERE, ASSETS[aid]["file_path"])).convert("RGBA")
        _spr[key] = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)  # uniform scale only
    return _spr[key]

def place_sprite(img, aid, cx, base_scale, lt):
    sp = sprite(aid, base_scale * pop(lt))
    img.paste(sp, (round(cx - sp.width / 2), H - sp.height + 6), sp)

def panel(d, box, fill=CREAM):
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0 + 10, y0 + 14, x1 + 10, y1 + 14), 34, fill=(12, 10, 14))
    d.rounded_rectangle(box, 34, fill=fill, outline=INK, width=6)

def card_static(d, sh, oy):
    """Everything on the card that does not animate. oy = slide offset."""
    t, X0, Y0, X1, Y1 = sh["type"], 110, 120 + oy, 1300, 960 + oy
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
        d.text((X0 + 70, y + 6), sh["where"], font=font(42, "SemiBold"), fill=MUTED)
        text_block(d, (X0 + 70, y + 90), sh["what"], font(48, "Medium"), X1 - X0 - 140, gap=1.3)
    if t == "curve":
        ax0, ay0, ax1, ay1 = X0 + 130, Y0 + 210, X1 - 90, Y1 - 120
        d.line((ax0, ay1, ax1, ay1), fill=INK, width=6); d.line((ax0, ay0, ax0, ay1), fill=INK, width=6)
        d.text(((ax0 + ax1) / 2 - 80, ay1 + 26), sh["x"], font=font(44, "Bold"), fill=INK)
        d.text((X0 + 40, ay0 - 70), sh["y"], font=font(44, "Bold"), fill=INK)

def card_dynamic(d, sh, lt, dur):
    """Animated parts: list reveals, growing bars, counting stats, the curve drawing."""
    t, X0, Y0, X1, Y1 = sh["type"], 110, 120, 1300, 960
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

def frame_for(seg, lt, dur, beat=0):
    sh = seg["show"]; t = sh["type"]
    fullscreen = t in ("char", "chapter", "end")
    img = background(sh["bg"], dim=not fullscreen or t != "char").copy()
    d = ImageDraw.Draw(img)
    oy = round((1 - ease(lt / 0.3)) * 60)
    card_static(d, sh, oy)
    if oy == 0: card_dynamic(d, sh, lt, dur)
    if t == "char": place_sprite(img, sh["sprite"], 1420, 3.1, lt)
    elif t in ("chapter", "end"): place_sprite(img, sh["sprite"], 1560, 2.6, lt)
    else: place_sprite(img, sh["sprite"], 1620, 2.0, lt)
    if t == "char":  # slow push-in keeps static shots alive
        z = (1.07 if beat % 2 else 1.0) + 0.025 * min(lt / max(dur, 0.1), 1)
        if z > 1.001:
            cw, ch = W / z, H / z
            img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
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
        if s["show"]["type"] == "chapter":
            a, b = int((tm["start"] - 0.8) * sr), int((tm["end"] + 0.6) * sr); out[max(a, 0):b] *= 0.0
    out = np.convolve(out, np.ones(60) / 60, "same")  # soften
    out = out / np.sqrt((out ** 2).mean() + 1e-9) * 10 ** (-40 / 20)  # ~24 dB under the -16 LUFS voice
    sys.path.insert(0, VOICE_DIR); import kokoro_tts as k; k.save(out.astype(np.float32), path)
    return path

# ---------- outputs ----------
def thumbnail(v, path):
    # MrBeast-style: 1 face big ("rule of big"), <=3 words that add to the title, simple saturated cool background,
    # rim-lit subject, white/yellow text with thick black stroke + hard shadow, top-left text, bottom-right corner free.
    from PIL import ImageFilter, ImageEnhance, ImageChops
    th = v["thumb"]; img = Image.open(os.path.join(HERE, BGS[th["bg"]]["file_path"])).convert("RGB").resize((1280, 720), Image.LANCZOS)
    img = ImageEnhance.Color(img.filter(ImageFilter.GaussianBlur(7))).enhance(1.6)
    img = Image.blend(img, Image.new("RGB", img.size, (24, 110, 190)), 0.28)  # teal/blue grade
    yy, xx = np.mgrid[0:720, 0:1280]; vig = 1 - 0.45 * (((xx - 900) / 900) ** 2 + ((yy - 360) / 520) ** 2).clip(0, 1)
    img = Image.fromarray((np.asarray(img) * vig[..., None]).astype(np.uint8))
    sp = Image.open(os.path.join(HERE, ASSETS[th["sprite"]]["file_path"])).convert("RGBA")
    sp = ImageEnhance.Color(sp.resize((round(sp.width * 3.15), round(sp.height * 3.15)), Image.LANCZOS)).enhance(1.25)
    # sprites are cropped at their image border: fade those cut edges so no straight lines show
    al = np.asarray(sp.split()[-1]).astype(float); h, w = al.shape; F = 60; ramp = np.linspace(0, 1, F)
    if al[:, 0].max() > 0: al[:, :F] *= ramp[None, :]
    if al[0, :].max() > 0: al[:F, :] *= ramp[:, None]
    if al[:, -1].max() > 0: al[:, -F:] *= ramp[::-1][None, :]
    P = 40; a = Image.new("L", (w + 2 * P, h + 2 * P)); a.paste(Image.fromarray(al.astype(np.uint8)), (P, P))
    sp.putalpha(Image.fromarray(al.astype(np.uint8))); x0, y0 = 1280 - w - 10, 720 - h + 150
    for grow, col in ((22, (0, 230, 255)), (10, (255, 255, 255))):  # cyan rim light, then white sticker edge
        rim = Image.new("RGBA", a.size, col + (0,)); rim.putalpha(a.point(lambda p: 255 if p > 128 else 0).filter(ImageFilter.MaxFilter(grow * 2 + 1)))
        if grow > 12: rim = rim.filter(ImageFilter.GaussianBlur(6))
        img.paste(rim, (x0 - P, y0 - P), rim)
    img.paste(sp, (x0, y0), sp)
    d = ImageDraw.Draw(img); y = 60; lines = th["text"].split("|")
    for i, ln in enumerate(lines):
        f = font(150 if len(ln) <= 7 else 124, "Black"); fill = (255, 230, 0) if i == len(lines) - 1 else (255, 255, 255)
        d.text((62, y + 10), ln, font=f, fill=(0, 0, 0), stroke_width=16, stroke_fill=(0, 0, 0))  # hard drop shadow
        d.text((50, y), ln, font=f, fill=fill, stroke_width=16, stroke_fill=(0, 0, 0)); y += f.size * 1.05
    img.save(path, quality=95)

def description(v, timing, series, path):
    def ts(s): s = int(s); return f"{s // 60}:{s % 60:02d}"
    chap = [("0:00", "Intro")] + [(ts(timing[i]["start"]), s["show"]["title"]) for i, s in enumerate(v["segments"]) if s["show"]["type"] == "chapter"]
    idx = [x["id"] for x in series].index(v["id"])
    nxt = series[idx + 1:idx + 4]
    lines = [v["desc"], "", "\u23f1 Chapters"] + [f"{a} {b}" for a, b in chap] + ["", "\U0001f52e Coming up next on the channel:"]
    lines += [f"\u25b8 {x['title']}" for x in nxt] + ["", "\U0001f4da Sources"] + [f"\u2022 {s}" for s in v["sources"]]
    lines += ["", "Narration is AI-generated (synthetic voice). Script, research and edit by the channel.", "", " ".join(v["tags"])]
    open(path, "w").write("\n".join(lines) + "\n")

if __name__ == "__main__":
    v = json.load(open(sys.argv[1])); validate(v)
    series = json.load(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "series.json")))
    wav, timing = voice(v)
    total = timing[-1]["end"]; N = round(total * FPS)
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    out = os.path.join(HERE, "renders", v["id"] + ".mp4"); silent = out[:-4] + "_silent.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    import wave
    w = wave.open(wav); va = np.abs(np.frombuffer(w.readframes(w.getnframes()), np.int16)); sr = w.getframerate()
    quiet = np.convolve(va > 300, np.ones(int(0.3 * sr)), "valid") == 0  # 0.3 s of silence = sentence gap
    beats = np.flatnonzero(np.diff(quiet.astype(int)) == -1) / sr + 0.3
    si = 0
    for f in range(N):
        t = f / FPS
        while si + 1 < len(timing) and t >= timing[si + 1]["start"]: si += 1
        seg, tm = v["segments"][si], timing[si]
        ff.stdin.write(frame_for(seg, t - tm["start"], tm["end"] - tm["start"], int(((beats > tm["start"] + 0.2) & (beats <= t)).sum())).tobytes())
        if f % (FPS * 30) == 0: print(f"video {t / total:5.1%}", flush=True)
    ff.stdin.close(); ff.wait()
    # sfx: soft whoosh on every card/chapter, pop on character scenes
    sfx = os.path.join(HERE, "..", "remotion", "public", "sfx"); ins, flt, lab = ["-i", wav], ["[1]loudnorm=I=-16:TP=-1.5[v]"], ["[v]"]
    for i, (s, tm) in enumerate(zip(v["segments"], timing)):
        if i == 0: continue
        ins += ["-i", os.path.join(sfx, {"char": "pop.wav", "stat": "boom.wav", "bars": "boom.wav"}.get(s["show"]["type"], "whoosh.wav"))]
        ms = round(tm["start"] * 1000); flt.append(f"[{len(lab) + 1}]adelay={ms}|{ms},volume=0.22[s{i}]"); lab.append(f"[s{i}]")
    ins += ["-i", music(total, timing, v, out[:-4] + "_music.wav")]; flt.append(f"[{len(lab) + 1}]anull[mu]"); lab.append("[mu]")
    flt.append("".join(lab) + f"amix=inputs={len(lab)}:normalize=0[m]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, *ins, "-filter_complex", ";".join(flt), "-map", "0:v", "-map", "[m]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", out], check=True)
    os.remove(silent); os.remove(out[:-4] + "_music.wav")
    thumbnail(v, out[:-4] + "_thumb.png"); description(v, timing, series, out[:-4] + "_description.txt")
    print(f"DONE {out} {total / 60:.2f} min")
