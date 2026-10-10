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

def captions(segs, timing, a, b, path):
    """Word-by-word pop-up captions (ASS). Word times are estimated inside each voiced segment by word length,
    with a short pause after sentence ends (the voice has no word timestamps)."""
    import re
    def ts(x): x = max(0, x); return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"
    ev = []
    for seg, tm in zip(segs, timing):
        if tm["end"] <= a or tm["start"] >= b: continue
        words = seg["say"].split(); w8 = [len(re.sub(r"\W", "", w)) + 2 + (5 if re.search(r"[.!?]$", w) else 0) for w in words]
        dur, t0 = (tm["end"] - tm["start"]) * 0.92, tm["start"]
        times = [t0 + dur * sum(w8[:i]) / sum(w8) for i in range(len(words) + 1)]
        for c in range(0, len(words), 3):  # chunks of 3 words, current word yellow + pop
            chunk = words[c:c + 3]
            for k in range(len(chunk)):
                i = c + k; s0, s1 = times[i] - a, (times[i + 1] if k < len(chunk) - 1 else times[min(c + 3, len(words))]) - a
                txt = " ".join(("{\\c&H5AF02E&\\fscx118\\fscy118\\t(0,90,\\fscx100\\fscy100)}" + w.upper() + "{\\c&HFFFFFF&}") if j == k else w.upper() for j, w in enumerate(chunk))
                if s1 > 0: ev.append(f"Dialogue: 0,{ts(s0)},{ts(min(s1, b - a))},W,,0,0,0,,{txt}")
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: W,Inter Black,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,9,0,2,60,60,430,1\n\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    open(path, "w").write(head + "\n".join(ev) + "\n")

def render(s):
    t = json.load(open(os.path.join(HERE, "audio", s["src"] + "_timing.json")))
    a = t[s["first"]]["start"]; last = s["first"]
    while last + 1 < len(t) and t[last + 1]["end"] - a <= s.get("max", 58) and last + 1 <= s.get("last", 999): last += 1
    b = t[last]["end"]
    v = json.load(open(os.path.join(HERE, "videos", s["src"] + ".json"))); full = v["title"]
    ov = os.path.join(HERE, "renders", s["id"] + "_ov.png"); overlay(s["top"], full, ov)
    cap = os.path.join(HERE, "renders", s["id"] + ".ass"); captions(v["segments"], t, a, b, cap)
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
