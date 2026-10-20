"""Animate one painted 9:16 panel (owner 20 Oct, Faith Doodles v3): layers (sky, drifting clouds, scene, foreground rocks),
camera move with slow-in/slow-out, parallax, impact shake + dust, English karaoke caption, title + progress bar.
Usage: python3 panel_anim.py panel.png out.mp4 "caption text" [seconds] [title]"""
import sys, os, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
src, out, cap = sys.argv[1:4]; dur = float(sys.argv[4]) if len(sys.argv) > 4 else 5; title = sys.argv[5] if len(sys.argv) > 5 else ""
FPS, W, H = 24, 1080, 1920
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cosmozibs", "engine", "fonts", "Poppins-Bold.ttf")
im = cv2.cvtColor(cv2.imread(src), cv2.COLOR_BGR2RGB); im = cv2.resize(im, (W, int(im.shape[0] * W / im.shape[1])), interpolation=cv2.INTER_CUBIC)
ih = im.shape[0]; a = im.astype(int); R, G, B = a[..., 0], a[..., 1], a[..., 2]
sky = (B > 200) & (R < 175) & (B - R > 70)
lab, nl = __import__('scipy.ndimage', fromlist=['label']).label(sky | ((a.min(2) > 228) & (np.arange(ih)[:, None] < ih * .35)))
top = set(np.unique(lab[:12])) - {0}; sky &= np.isin(lab, list(top))          # only sky connected to the top edge (never an eye white)
cloud = (a.min(2) > 228) & (np.arange(ih)[:, None] < ih * .35) & np.isin(lab, list(top))
cloud = cv2.morphologyEx(cloud.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)).astype(bool)
rocks = (np.arange(ih)[:, None] > ih * .82) & (a.max(2) < 120)
rocks = cv2.dilate(rocks.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
skyplate = cv2.inpaint(im, ((~sky).astype(np.uint8) * 255), 5, cv2.INPAINT_TELEA) if False else None
# sky plate: vertical gradient sampled from the sky pixels (clean, can move freely)
rows = [im[y][sky[y]].mean(0) if sky[y].sum() > 20 else None for y in range(ih)]
last = np.array([120, 213, 252.]); plate = np.zeros_like(im, dtype=np.float32)
for y in range(ih): last = rows[y] if rows[y] is not None else last; plate[y] = last
plate = plate.astype(np.uint8)
def rgba(mask, img=im): return np.dstack([img, (mask * 255).astype(np.uint8)])
L_cloud = rgba(cloud); L_scene = rgba(~sky & ~cloud); L_rock = rgba(rocks)
def place(layer, scale, cx, cy, canvas):   # scale around (cx, cy) in panel coords -> screen centre
    M = np.float32([[scale, 0, W / 2 - cx * scale], [0, scale, H / 2 - cy * scale]])
    warped = cv2.warpAffine(layer, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    al = warped[..., 3:4] / 255.; canvas[:] = canvas * (1 - al) + warped[..., :3] * al
ease = lambda u: u * u * (3 - 2 * u)
font = ImageFont.truetype(FONT, 78); tfont = ImageFont.truetype(FONT, 50)
words = cap.split(); n = int(dur * FPS)
dust = [(np.random.RandomState(i).rand() * W, np.random.RandomState(i + 99).rand()) for i in range(40)]
os.makedirs("/tmp/pa", exist_ok=True)
for f in range(n):
    t = f / FPS; u = ease(min(1, max(0, (t - .3) / (dur - 1.0))))
    # camera: wide on David -> tilt up and push in on the giant's face (slow-in/slow-out)
    sc = 1.0 + .32 * u; cx = W / 2 + 70 * u; cy = ih / 2 - 520 * u
    hw, hh = W / 2 / sc, H / 2 / sc; cx = min(max(cx, hw), W - hw); cy = min(max(cy, hh), ih - hh)   # never show past the painting
    shake = 0
    if t > 3.0: k = t - 3.0; shake = 14 * np.exp(-k * 7) * np.sin(k * 60)
    cy += shake
    fr = np.zeros((H, W, 3), np.float32)
    place(np.dstack([plate, np.full(plate.shape[:2], 255, np.uint8)]), sc * .97, cx * .98, cy * .9, fr)   # sky: slower (parallax)
    drift = t * 18
    place(L_cloud, sc * .98, cx * .98 - drift, cy * .92, fr)
    place(L_scene, sc * (1 + .004 * np.sin(t * 2.2)), cx, cy, fr)                                       # scene: subtle breathing
    place(L_rock, sc * 1.10, cx + (cx - W / 2) * .3, cy + 40 * u, fr)                                    # foreground: faster (parallax)
    img = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img, "RGBA")
    if t > 3.0:   # impact dust puffs at the giant's feet
        k = t - 3.0
        for i in range(10):
            ang = np.pi * (i / 9); r = 40 + k * 260; x = W * .66 + np.cos(ang) * r * 1.4; y = H * .62 - np.sin(ang) * r * .35 + 140 * u
            rr = 34 * (1 - min(1, k / 1.6)) + 4; d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(235, 210, 170, int(200 * max(0, 1 - k / 1.6))), outline=(40, 30, 20, int(160 * max(0, 1 - k / 1.6))), width=4)
    for i, (dx, dy) in enumerate(dust):   # floating dust motes
        y = (dy * H - t * (20 + i % 5 * 8)) % H; x = dx + np.sin(t + i) * 10; d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 245, 220, 110))
    # title + progress bar (same TikTok edit as the other channels)
    if title:
        d.text((W / 2, 210), title, font=tfont, fill="white", anchor="mm", stroke_width=7, stroke_fill="#1b1b1b")
        d.rounded_rectangle([90, 262, 990, 276], 7, fill=(0, 0, 0, 90)); d.rounded_rectangle([90, 262, 90 + 900 * t / dur, 276], 7, fill="#f9d65c")
    # karaoke caption, word by word with a pop
    ws = max(0, min(len(words), int((t - .2) / ((dur - .8) / len(words))) + 1))
    lines, cur = [], []
    for j, w_ in enumerate(words[:ws]):
        if cur and len(" ".join(words[k] for k in cur + [j])) > 16: lines.append(cur); cur = []
        cur.append(j)
    if cur: lines.append(cur)
    pop = 1 + .12 * max(0, 1 - ((t - .2) % ((dur - .8) / len(words))) / .12)
    for li, idx in enumerate(lines[-2:]):
        fnt = ImageFont.truetype(FONT, int(86 * (pop if ws - 1 in idx else 1)))
        x0 = W / 2 - d.textlength(" ".join(words[k] for k in idx), font=fnt) / 2; y = 1330 + li * 100 - (len(lines[-2:]) - 1) * 50
        for k in idx:
            d.text((x0, y), words[k], font=fnt, fill="#f9d65c" if k == ws - 1 else "white", anchor="ls", stroke_width=11, stroke_fill="#1b1b1b"); x0 += d.textlength(words[k] + " ", font=fnt)
    img.save(f"/tmp/pa/f{f:04d}.png")
# sound: wind bed + whoosh on the camera move + thud on the impact (procedural)
sr = 44100; tt = np.arange(int(dur * sr)) / sr; rng = np.random.RandomState(1)
noise = np.convolve(rng.randn(len(tt)), np.ones(300) / 300, "same")
wind = noise * .6 * (0.6 + .4 * np.sin(tt * .7)); wh = noise * 3 * np.exp(-((tt - 1.4) / .5) ** 2)
thud = np.zeros_like(tt); m = tt > 3.0; k = tt[m] - 3.0; thud[m] = np.sin(2 * np.pi * (55 - 20 * k) * k) * np.exp(-k * 5) * .9
au = wind * .4 + wh * .5 + thud; au = au / np.abs(au).max() * .8
import wave; wf = wave.open("/tmp/pa/a.wav", "w"); wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes((au * 32767).astype(np.int16).tobytes()); wf.close()
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", "/tmp/pa/f%04d.png",
  "-f", "lavfi", "-i", "color=c=0x808080:s=36x64:r=12,noise=c0s=60:allf=t,lutyuv=y=128+(val-128)*0.035,scale=1080:1920:flags=bicubic,fps=24",
  "-f", "lavfi", "-i", "color=c=0x808080:s=36x64:r=12,noise=c0s=60:allf=t+u,lutyuv=y=128+(val-128)*0.035,scale=1080:1920:flags=bicubic,fps=24",
  "-i", "/tmp/pa/a.wav", "-filter_complex", "[0:v][1:v][2:v]displace=edge=smear,format=yuv420p[v]", "-map", "[v]", "-map", "3:a",
  "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-shortest", "-movflags", "+faststart", out], check=True)
print("done", out)
