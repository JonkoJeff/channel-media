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
    """Thumbnail-style opening frame (first 1.7 s): the character with a coloured glow + big hook text, so any auto-picked frame (Zernio takes 1.5 s) is a real thumbnail.
    Own colour per Short (ACCENTS), background and sprite from the Short's first scene."""
    import zlib
    import numpy as np
    from PIL import ImageEnhance, ImageFilter
    sh = v["segments"][s["first"]]["show"]; acc = ACCENTS[zlib.crc32(s["id"].encode()) % len(ACCENTS)]
    bgid = sh.get("bg") if sh.get("bg") in BGS else "bedroom_night"; spr = sh.get("sprite") if sh.get("sprite") in ASSETS else "A10"
    if spr[0] in "AN": spr = pick_sprite(s["id"], spr)
    bg = Image.open(os.path.join(CH, BGS[bgid]["file_path"])).convert("RGB"); r = max(1080 / bg.width, 1920 / bg.height)
    bg = bg.resize((round(bg.width * r), round(bg.height * r)), Image.LANCZOS); bg = bg.crop(((bg.width - 1080) // 2, (bg.height - 1920) // 2, (bg.width - 1080) // 2 + 1080, (bg.height - 1920) // 2 + 1920))
    img = ImageEnhance.Color(bg.filter(ImageFilter.GaussianBlur(9))).enhance(1.5); img = Image.blend(img, Image.new("RGB", img.size, (255, 140, 50)), 0.2)
    yy, xx = np.mgrid[0:1920, 0:1080]; img = Image.fromarray((np.asarray(img) * (1 - 0.5 * (((xx - 540) / 700) ** 2 + ((yy - 1100) / 1300) ** 2).clip(0, 1))[..., None]).astype(np.uint8))
    hd = os.path.join(CH, "assets_hd", os.path.basename(ASSETS[spr]["file_path"])); k = 4 if os.path.exists(hd) else 1
    sp = Image.open(hd if k == 4 else os.path.join(CH, ASSETS[spr]["file_path"])).convert("RGBA"); sc = 1000 / sp.width * k
    sp = ImageEnhance.Color(sp.resize((1000, round(sp.height * sc / k)), Image.LANCZOS)).enhance(1.25)
    al = np.asarray(sp.split()[-1]).astype(float); h, w = al.shape; F = 60; ramp = np.linspace(0, 1, F)
    if al[:, 0].max() > 0: al[:, :F] *= ramp[None, :]
    if al[0, :].max() > 0: al[:F, :] *= ramp[:, None]
    if al[:, -1].max() > 0: al[:, -F:] *= ramp[::-1][None, :]
    P = 40; a = Image.new("L", (w + 2 * P, h + 2 * P)); a.paste(Image.fromarray(al.astype(np.uint8)), (P, P)); sp.putalpha(Image.fromarray(al.astype(np.uint8)))
    x0, y0 = 40, 1920 - h + 120
    for grow, col in ((22, acc), (10, (255, 255, 255))):  # glow in the Short's colour, then white sticker edge
        rim = Image.new("RGBA", a.size, col + (0,)); rim.putalpha(a.point(lambda p: 255 if p > 128 else 0).filter(ImageFilter.MaxFilter(grow * 2 + 1)))
        if grow > 12: rim = rim.filter(ImageFilter.GaussianBlur(6))
        img.paste(rim, (x0 - P, y0 - P), rim)
    img.paste(sp, (x0, y0), sp)
    d = ImageDraw.Draw(img); f = font(132, "Black"); lines = wrap(d, s["top"].rstrip(":").upper(), f, 980)[:4]; y = 150
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=f); L = (1080 - tw) / 2
        if i == len(lines) - 1 and len(lines) > 1:  # last line on a colour block
            d.rounded_rectangle((L - 18 + 10, y + 22 + 10, L + tw + 28 + 10, y + 150 + 10), 24, fill=(0, 0, 0)); d.rounded_rectangle((L - 28, y + 10, L + tw + 28, y + 150), 24, fill=acc, outline=(0, 0, 0), width=8)
            d.text((L, y), ln, font=f, fill=(28, 20, 14)); y += 150; continue
        d.text((L + 8, y + 8), ln, font=f, fill=(0, 0, 0), stroke_width=14, stroke_fill=(0, 0, 0)); d.text((L, y), ln, font=f, fill=(255, 255, 255), stroke_width=14, stroke_fill=(0, 0, 0)); y += 150
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
    cv = os.path.join(HERE, "renders", s["id"] + "_cover.png"); cover(s, v, cv)
    cap = os.path.join(HERE, "renders", s["id"] + ".ass"); captions(v["segments"], t, a, b, cap, spans=sentence_spans(os.path.join(HERE, "audio", s["src"] + "_vo.wav"), v["segments"], t))
    out = os.path.join(HERE, "renders", s["id"] + ".mp4")
    fc = ("[0:v]split[a][b];[a]scale=-2:1920,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.18[bg];"
          "[b]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2[v];[v][1:v]overlay=0:0[v2];[v2][2:v]overlay=0:0:enable='lt(t,1.7)',ass=" + cap + "[out]")   # cover (thumbnail look) on screen for the first 1.7 s
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", os.path.join(HERE, "renders", s["src"] + ".mp4"),
                    "-i", ov, "-i", cv, "-filter_complex", fc, "-map", "[out]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", out], check=True)
    os.remove(ov); os.remove(cv); os.remove(cap)
    assert b - a <= 60, f"{s['id']} too long for a Short: {b - a:.1f}s"
    print(f"{s['id']}: {s['src']} segs {s['first']}-{last}, {b - a:.1f}s")
    return out

if __name__ == "__main__":
    for s in json.load(open(sys.argv[1])): render(s)
