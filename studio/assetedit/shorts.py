"""Cut vertical Shorts (1080x1920) out of finished long-form videos: hook text on top, the clip in the middle, nothing else (the link to the full video goes in the description).
Usage: python3 shorts.py videos/shorts.json   -> renders/<short_id>.mp4
A short = whole segments [first..last] of a long video (cut on voice boundaries), max ~58 s."""
import json, os, subprocess, sys
from PIL import Image, ImageDraw
from longform import pick_sprite, font, wrap, INK, CREAM, HERE, ASSETS, BGS, CH, ACCENTS

def overlay(top, full_title, path):
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = font(84, "Black"); y = 250
    for ln in wrap(d, top, f, 960):
        d.text((540 - d.textlength(ln, font=f) / 2, y), ln, font=f, fill=CREAM, stroke_width=10, stroke_fill=INK); y += 96
    im.save(path)

def cover(s, v, path):
    """Thumbnail-style opening frame (first 1.7 s): character with a coloured glow + big hook text, so any auto-picked frame (Zernio takes 1.5 s) is a real thumbnail.
    Owner 18 Oct: they all looked alike -> per Short (crc of its id) a different approved background (mirrored or not, own tint), pose (pick_sprite), side, size, tilt,
    text alignment/size, spotlight and accent colour."""
    import zlib
    import numpy as np
    from PIL import ImageEnhance, ImageFilter
    crc = zlib.crc32(s["id"].encode()); acc = (ACCENTS + [(70, 220, 110), (170, 230, 50), (255, 200, 40)])[crc % 12]; lay = (crc >> 7) % 4
    sh = v["segments"][s["first"]]["show"]; spr = sh.get("sprite") if sh.get("sprite") in ASSETS else "A10"
    if spr[0] in "AN": spr = pick_sprite(s["id"], spr, True)
    emo = ASSETS[spr].get("emotion"); ok = sorted(b for b, x in BGS.items() if x.get("approved") and (emo is None or emo in x["emotions"])) or ["bedroom_night"]
    bgid = ok[(crc >> 3) % len(ok)]
    bg = Image.open(os.path.join(CH, BGS[bgid]["file_path"])).convert("RGB")
    if (crc >> 5) & 1: bg = bg.transpose(Image.FLIP_LEFT_RIGHT)
    r = max(1080 / bg.width, 1920 / bg.height) * (1.0 + 0.12 * ((crc >> 9) % 3))   # zoom 1.0 / 1.12 / 1.24 on another part of the room
    bg = bg.resize((round(bg.width * r), round(bg.height * r)), Image.LANCZOS); ox = ((bg.width - 1080) * (((crc >> 11) % 3) / 2)); bg = bg.crop((int(ox), (bg.height - 1920) // 2, int(ox) + 1080, (bg.height - 1920) // 2 + 1920))
    HUES = [(235, 60, 60), (255, 130, 30), (250, 215, 40), (140, 215, 50), (40, 200, 90), (30, 190, 170), (50, 140, 255), (120, 90, 240), (200, 70, 220), (255, 90, 150)]   # owner 18 Oct: more colours incl. green/orange/yellow
    hi = (crc >> 13) % 10; tint = HUES[hi]
    img = ImageEnhance.Color(bg.filter(ImageFilter.GaussianBlur(6))).enhance(0.7)
    tint2 = HUES[(hi + 1 + (crc >> 17) % 3) % 10]
    gr = np.clip((yy_ := np.mgrid[0:1920, 0:1080][0]) / 1920.0, 0, 1)[..., None]
    tg = np.array(tint)[None, None, :] * (1 - gr) + np.array(tint2)[None, None, :] * gr
    img = Image.fromarray((np.asarray(img) * 0.42 + tg * 0.58).clip(0, 255).astype(np.uint8))
    yy, xx = np.mgrid[0:1920, 0:1080]; img = Image.fromarray((np.asarray(img) * (1 - 0.5 * (((xx - 540) / 700) ** 2 + ((yy - 1100) / 1300) ** 2).clip(0, 1))[..., None]).astype(np.uint8))
    hd = os.path.join(CH, "assets_hd", os.path.basename(ASSETS[spr]["file_path"])); k = 4 if os.path.exists(hd) else 1
    sp = Image.open(hd if k == 4 else os.path.join(CH, ASSETS[spr]["file_path"])).convert("RGBA"); fs = (132, 120, 148, 126)[lay]; txt = s["top"].rstrip(":").upper(); d0 = ImageDraw.Draw(Image.new("L", (8, 8)))
    while True:
        f = font(fs, "Black"); lines = wrap(d0, txt, f, 900)[:4]
        if max(d0.textlength(l, font=f) for l in lines) <= 930 or fs < 70: break
        fs -= 8
    step = int(fs * 1.14); th = len(lines) * step
    W0 = int(max(760, min(1200, (1920 + 90 - (150 + th + 24)) * sp.width / sp.height))); sc = W0 / sp.width * k   # owner 18 Oct: no empty middle -> character as big as fits under the text
    sp = ImageEnhance.Color(sp.resize((W0, round(sp.height * sc / k)), Image.LANCZOS)).enhance(1.25)
    tilt = 0   # owner 18 Oct: no flying/tilted characters, they stand on the bottom edge
    if tilt:
        sp = sp.rotate(tilt, expand=True, resample=Image.BICUBIC)
    al = np.asarray(sp.split()[-1]).astype(float); h, w = al.shape; F = 60; ramp = np.linspace(0, 1, F)
    if al[:, 0].max() > 0: al[:, :F] *= ramp[None, :]
    if al[0, :].max() > 0: al[:F, :] *= ramp[:, None]
    if al[:, -1].max() > 0: al[:, -F:] *= ramp[::-1][None, :]
    P = 40; a = Image.new("L", (w + 2 * P, h + 2 * P)); a.paste(Image.fromarray(al.astype(np.uint8)), (P, P)); sp.putalpha(Image.fromarray(al.astype(np.uint8)))
    x0 = (40, 1080 - w - 40, (1080 - w) // 2, 1080 - w - 20)[lay] if w <= 1080 else (-40, 1080 - w + 40, (1080 - w) // 2, (1080 - w) // 2 + 30)[lay]; y0 = 1920 - h + 90
    cx, cy = x0 + w // 2, y0 + h // 3   # spotlight in the accent colour behind the character
    spot = np.clip(1 - np.hypot((xx - cx) / 560, (yy - cy) / 640), 0, 1) ** 1.6 * 0.55
    img = Image.fromarray((np.asarray(img) * (1 - spot[..., None]) + np.array(acc) * spot[..., None]).clip(0, 255).astype(np.uint8))
    for grow, col in ((22, acc), (10, (255, 255, 255))):  # glow in the Short's colour, then white sticker edge
        rim = Image.new("RGBA", a.size, col + (0,)); rim.putalpha(a.point(lambda p: 255 if p > 128 else 0).filter(ImageFilter.MaxFilter(grow * 2 + 1)))
        if grow > 12: rim = rim.filter(ImageFilter.GaussianBlur(6))
        img.paste(rim, (x0 - P, y0 - P), rim)
    img.paste(sp, (x0, y0), sp)
    d = ImageDraw.Draw(img); f = font(fs, "Black"); y = int(max(150, min(y0 - th - 24, 330)))
    align = ("c", "l", "c", "r")[lay]
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=f); L = {"c": (1080 - tw) / 2, "l": 70, "r": 1010 - tw}[align]
        if i == len(lines) - 1 and len(lines) > 1:  # last line on a colour block
            d.rounded_rectangle((L - 18 + 10, y + 22 + 10, L + tw + 28 + 10, y + step + 10), 24, fill=(0, 0, 0)); d.rounded_rectangle((L - 28, y + 10, L + tw + 28, y + step), 24, fill=acc, outline=(0, 0, 0), width=8)
            d.text((L, y), ln, font=f, fill=(28, 20, 14)); y += step; continue
        d.text((L + 8, y + 8), ln, font=f, fill=(0, 0, 0), stroke_width=14, stroke_fill=(0, 0, 0)); d.text((L, y), ln, font=f, fill=(255, 255, 255), stroke_width=14, stroke_fill=(0, 0, 0)); y += step
    img.save(path)

def sentence_spans(wav, segs, timing):
    """Real sentence times, measured from the audio: inside each segment the (n-1) longest silences are the sentence boundaries.
    Returns {segment index: [(t0, t1) per sentence]}; segments where it cannot be measured are left out (caller falls back to estimates)."""
    import re, wave
    import numpy as np
    try: w = wave.open(wav)
    except Exception: return {}
    sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32); hop = int(0.01 * sr)
    rms = np.sqrt(np.convolve(x[:len(x) // hop * hop] ** 2, np.ones(hop) / hop, "valid")[::hop]) if len(x) > hop else np.zeros(1)
    loud = rms > max(150.0, 0.02 * float(np.percentile(rms, 98))); out = {}
    for i, (seg, tm) in enumerate(zip(segs, timing)):
        n = len(re.split(r"(?<=[.!?])\s+", seg["say"].strip()))
        a, b = int(tm["start"] * 100), min(int(tm["end"] * 100), len(loud)); idx = np.flatnonzero(loud[a:b])
        if not len(idx): continue
        f0, f1 = a + idx[0], a + idx[-1] + 1; runs, k = [], f0
        while k < f1:
            if loud[k]: k += 1; continue
            j = k
            while j < f1 and not loud[j]: j += 1
            if j - k >= 8: runs.append((j - k, k, j))   # silence >= 80 ms
            k = j
        if len(runs) < n - 1: continue
        cut = sorted(sorted(runs, reverse=True)[:n - 1], key=lambda r: r[1]); edges = [f0] + [e for r in cut for e in (r[1], r[2])] + [f1]
        out[i] = [(edges[2 * q] / 100, edges[2 * q + 1] / 100) for q in range(n)]
    return out

def captions(segs, timing, a, b, path, res=(1080, 1920), size=84, outline=9, marginv=430, ml=60, mr=60, calm=False, spans=None):
    """Word-by-word pop-up captions (ASS). With `spans` (sentence_spans) every sentence is timed from the measured audio and only the words
    inside a sentence are estimated (by length, extra weight after commas); without it the whole segment is estimated (drifts)."""
    import re
    def ts(x): x = max(0, x); return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"
    def wt(w): return len(re.sub(r"\W", "", w)) + 2 + (3 if re.search(r"[,;:]$", w) else 0)
    ev = []
    for si, (seg, tm) in enumerate(zip(segs, timing)):
        if tm["end"] <= a or tm["start"] >= b: continue
        words = seg["say"].split()
        starts = None
        if spans and si in spans:
            sents = re.split(r"(?<=[.!?])\s+", seg["say"].strip()); st, en = [], []
            for sent, (t0, t1) in zip(sents, spans[si]):
                ws = sent.split(); w8 = [wt(w) for w in ws]; tot = sum(w8) or 1
                for r in range(len(ws)): st.append(t0 + (t1 - t0) * sum(w8[:r]) / tot); en.append(t0 + (t1 - t0) * sum(w8[:r + 1]) / tot)
            if len(st) == len(words): starts, ends_ = st, en
        if starts is None:
            w8 = [len(re.sub(r"\W", "", w)) + 2 + (5 if re.search(r"[.!?]$", w) else 0) for w in words]
            dur, t0 = (tm["end"] - tm["start"]) * 0.92, tm["start"]
            tt = [t0 + dur * sum(w8[:i]) / sum(w8) for i in range(len(words) + 1)]; starts, ends_ = tt[:-1], tt[1:]
        for c in range(0, len(words), 3):  # chunks of 3 words, current word highlighted
            chunk = words[c:c + 3]
            for k in range(len(chunk)):
                i = c + k; s0 = starts[i] - a
                s1 = (min(starts[i + 1], ends_[i] + 0.25) if k < len(chunk) - 1 and i + 1 < len(words) else ends_[min(c + 2, len(words) - 1)]) - a   # no caption hangs through a pause
                s1 = max(s1, s0 + 0.12)
                hl = "{\\c&H7AC8FF&}" if calm else "{\\c&H5AF02E&\\fscx118\\fscy118\\t(0,90,\\fscx100\\fscy100)}"  # calm: warm amber, no pop
                txt = " ".join((hl + (w if calm else w.upper()) + "{\\c&HFFFFFF&}") if j == k else (w if calm else w.upper()) for j, w in enumerate(chunk))
                if s1 > 0: ev.append(f"Dialogue: 0,{ts(s0)},{ts(min(s1, b - a))},W,,0,0,0,,{txt}")
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {res[0]}\nPlayResY: {res[1]}\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: W,Inter Black,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,{outline},0,2,{ml},{mr},{marginv},1\n\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    open(path, "w").write(head + "\n".join(ev) + "\n")

def render(s):
    t = json.load(open(os.path.join(HERE, "audio", s["src"] + "_timing.json")))
    a = t[s["first"]]["start"]; last = s["first"]
    while last + 1 < len(t) and t[last + 1]["end"] - a <= s.get("max", 58) and last + 1 <= s.get("last", 999): last += 1
    b = t[last]["end"]
    v = json.load(open(os.path.join(HERE, "videos", s["src"] + ".json"))); full = v.get("title", "")
    ov = os.path.join(HERE, "renders", s["id"] + "_ov.png"); overlay(s["top"], full, ov)
    cx = os.path.join(HERE, "..", "covers", s["id"] + ".jpg")   # cover painted by Codex (factory cf_cover), else the drawn one
    cv = cx   # owner 18 Oct: BAD covers are always the drawn varied ones (Codex covers all had the same peeking pose) -> written to studio/covers/<id>.jpg, also used as the post thumbnail
    cover(s, v, cv)
    cap = os.path.join(HERE, "renders", s["id"] + ".ass"); captions(v["segments"], t, a, b, cap, spans=sentence_spans(os.path.join(HERE, "audio", s["src"] + "_vo.wav"), v["segments"], t))
    out = os.path.join(HERE, "renders", s["id"] + ".mp4")
    fc = ("[0:v]split[a][b];[a]scale=-2:1920,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.18[bg];"
          "[b]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2[v];[v][1:v]overlay=0:0[v2];[v2][2:v]overlay=0:0:enable='lt(t,1.7)',ass=" + cap + "[out]")   # cover (thumbnail look) on screen for the first 1.7 s
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", os.path.join(HERE, "renders", s["src"] + ".mp4"),
                    "-i", ov, "-i", cv, "-filter_complex", fc, "-map", "[out]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", out], check=True)
    os.remove(ov); os.remove(cap)
    if cv != cx: os.remove(cv)
    assert b - a <= 60, f"{s['id']} too long for a Short: {b - a:.1f}s"
    print(f"{s['id']}: {s['src']} segs {s['first']}-{last}, {b - a:.1f}s")
    return out

if __name__ == "__main__":
    for s in json.load(open(sys.argv[1])): render(s)
