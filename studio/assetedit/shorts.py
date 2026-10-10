"""Cut vertical Shorts (1080x1920) out of finished long-form videos, each pointing to its full video.
Usage: python3 shorts.py videos/shorts.json   -> renders/<short_id>.mp4
A short = whole segments [first..last] of a long video (cut on voice boundaries), max ~58 s."""
import json, os, subprocess, sys
from PIL import Image, ImageDraw
from longform import font, wrap, INK, CREAM, ORANGE, HERE

def overlay(top, full_title, path):
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = font(84, "Black"); y = 250
    for ln in wrap(d, top, f, 960):
        d.text((540 - d.textlength(ln, font=f) / 2, y), ln, font=f, fill=CREAM, stroke_width=10, stroke_fill=INK); y += 96
    # bottom call-to-action, kept above the Shorts UI (bottom ~340 px)
    d.rounded_rectangle((60, 1260, 1020, 1540), 36, fill=ORANGE, outline=INK, width=8)
    d.text((100, 1290), "FULL VIDEO ON THE CHANNEL ▶", font=font(46, "Black"), fill=INK)
    y = 1360
    for ln in wrap(d, full_title, font(48, "Bold"), 880)[:3]:
        d.text((100, y), ln, font=font(48, "Bold"), fill=INK); y += 56
    im.save(path)

def render(s):
    t = json.load(open(os.path.join(HERE, "audio", s["src"] + "_timing.json")))
    a = t[s["first"]]["start"]; last = s["first"]
    while last + 1 < len(t) and t[last + 1]["end"] - a <= s.get("max", 58) and last + 1 <= s.get("last", 999): last += 1
    b = t[last]["end"]
    full = json.load(open(os.path.join(HERE, "videos", s["src"] + ".json")))["title"]
    ov = os.path.join(HERE, "renders", s["id"] + "_ov.png"); overlay(s["top"], full, ov)
    out = os.path.join(HERE, "renders", s["id"] + ".mp4")
    fc = ("[0:v]split[a][b];[a]scale=-2:1920,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.18[bg];"
          "[b]scale=1080:-2[fg];[bg][fg]overlay=0:620[v];[v][1:v]overlay=0:0,fade=t=in:d=0.15[out]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", os.path.join(HERE, "renders", s["src"] + ".mp4"),
                    "-i", ov, "-filter_complex", fc, "-map", "[out]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", out], check=True)
    os.remove(ov)
    assert b - a <= 60, f"{s['id']} too long for a Short: {b - a:.1f}s"
    print(f"{s['id']}: {s['src']} segs {s['first']}-{last}, {b - a:.1f}s")
    return out

if __name__ == "__main__":
    for s in json.load(open(sys.argv[1])): render(s)
