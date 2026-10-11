"""Assemble a 2.5 h video from its rendered parts.
videos/<id>.json = {"id", "title", "desc", "tags", "sources", "thumb", "parts": ["<id>_p01", ...]}; each part is a normal
video JSON with "part": true (first segment of every part is a `chapter`; part 1 opens with the hook, the last part ends with `end`).
Usage: python3 mega.py videos/<id>.json  -> renders/<id>.mp4 (+ _thumb.png, _description.txt, _frames/*.jpg)
Size: without studio/yt/APPROVED the file must fit Metricool (500 MB) -> 720p at a computed bitrate; with it -> 1080p CRF 21."""
import json, os, subprocess, sys
import longform as L
v = json.load(open(sys.argv[1])); R = os.path.join(L.HERE, "renders"); out = os.path.join(R, v["id"] + ".mp4")
segs, timing, off, lst = [], [], 0.0, os.path.join(R, v["id"] + "_list.txt")
with open(lst, "w") as f:
    for pid in v["parts"]:
        p = json.load(open(os.path.join(L.HERE, "videos", pid + ".json"))); t = json.load(open(os.path.join(L.HERE, "audio", pid + "_timing.json")))
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", os.path.join(R, pid + ".mp4")]))
        segs += p["segments"]; timing += [{"start": x["start"] + off, "end": x["end"] + off} for x in t]; off += dur
        f.write(f"file '{os.path.join(R, pid + '.mp4')}'\n")
total = off
approved = os.path.exists(os.path.join(L.HERE, "..", "yt", "APPROVED"))
src = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst]
if approved:
    subprocess.run([*src, "-c:v", "libx264", "-preset", "medium", "-tune", "animation", "-crf", "21", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
else:  # Metricool takes max 500 MB: 2-pass 720p at the bitrate that fits (tested: still sharp at ~330 kbps for this style)
    kbps = min(int(470 * 8 * 1024 / total) - 96, 4000)
    enc = ["-vf", "scale=1280:720", "-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-b:v", f"{kbps}k", "-pix_fmt", "yuv420p", "-passlogfile", out[:-4] + "_2pass"]
    subprocess.run([*src, *enc, "-pass", "1", "-an", "-f", "null", "/dev/null"], check=True)
    subprocess.run([*src, *enc, "-pass", "2", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out], check=True)
os.remove(lst)
mv = dict(v, segments=segs)
series = json.load(open(os.path.join(L.HERE, "videos", "series.json")))
if v["id"] not in [x["id"] for x in series]: series.append({"id": v["id"], "title": v["title"]})
L.thumbnail(mv, out[:-4] + "_thumb.png"); L.description(mv, timing, series, out[:-4] + "_description.txt")
fr = out[:-4] + "_frames"; os.makedirs(fr, exist_ok=True)
for i in range(12):  # review frames spread over the whole video
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{total * (i + 0.5) / 12:.1f}", "-i", out, "-frames:v", "1", "-vf", "scale=960:-1", os.path.join(fr, f"{i:02d}.jpg")], check=True)
mb = os.path.getsize(out) / 1e6
print(f"DONE {out} {total / 3600:.2f} h, {mb:.0f} MB, {'1080p' if approved else '720p'}")
if not approved and mb > 500: sys.exit("too big for Metricool")
