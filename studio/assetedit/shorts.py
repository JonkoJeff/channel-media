"""Cut vertical Shorts (1080x1920) out of finished long-form videos: hook text on top, the clip in the middle, nothing else (the link to the full video goes in the description).
Usage: python3 shorts.py videos/shorts.json   -> renders/<short_id>.mp4
A short = whole segments [first..last] of a long video (cut on voice boundaries), max ~58 s."""
import json, os, subprocess, sys
from PIL import Image, ImageDraw
from longform import font, wrap, INK, CREAM, HERE

def overlay(top, full_title, path):
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = font(84, "Black"); y = 250
    for ln in wrap(d, top, f, 960):
        d.text((540 - d.textlength(ln, font=f) / 2, y), ln, font=f, fill=CREAM, stroke_width=10, stroke_fill=INK); y += 96
    im.save(path)

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
    cap = os.path.join(HERE, "renders", s["id"] + ".ass"); captions(v["segments"], t, a, b, cap, spans=sentence_spans(os.path.join(HERE, "audio", s["src"] + "_vo.wav"), v["segments"], t))
    out = os.path.join(HERE, "renders", s["id"] + ".mp4")
    fc = ("[0:v]split[a][b];[a]scale=-2:1920,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.18[bg];"
          "[b]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2[v];[v][1:v]overlay=0:0,ass=" + cap + ",fade=t=in:d=0.15[out]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", os.path.join(HERE, "renders", s["src"] + ".mp4"),
                    "-i", ov, "-filter_complex", fc, "-map", "[out]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", out], check=True)
    os.remove(ov); os.remove(cap)
    assert b - a <= 60, f"{s['id']} too long for a Short: {b - a:.1f}s"
    print(f"{s['id']}: {s['src']} segs {s['first']}-{last}, {b - a:.1f}s")
    return out

if __name__ == "__main__":
    for s in json.load(open(sys.argv[1])): render(s)
