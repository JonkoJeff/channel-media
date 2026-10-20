"""Faith Doodles short from painted shots (owner 20 Oct: the approved still-frame style, several shots in a row).
Usage: python3 panel_short.py episode.json timeline.json voice.wav out.mp4
Each line of the episode has "panel" (file in panels/), "cam" (tiltup | pushin | pullout | panright | panleft | shake), optional "focus" [x, y] (0-1),
"layout" ("full" for 9:16 paintings, "card" for wide shots shown as a card over a blurred copy). Timing comes from the voice timeline."""
import sys, os, json, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
epf, tlf, wav, out = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__)); FPS, W, H = 24, 1080, 1920
FONT = os.path.join(HERE, "..", "..", "cosmozibs", "engine", "fonts", "Poppins-Bold.ttf")
ep = json.load(open(epf)); tl = json.load(open(tlf)); lines = [l for s in ep["segments"] for l in s["lines"]]; T = tl["lines"]; total = tl["total"]
ease = lambda u: u * u * (3 - 2 * u)
cache = {}
def load(name, layout):
    if name in cache: return cache[name]
    im = cv2.cvtColor(cv2.imread(os.path.join(HERE, "panels", name)), cv2.COLOR_BGR2RGB)
    if layout == "card":   # wide shot: blurred cover background + sharp upscaled card
        bg = cv2.resize(im, (int(im.shape[1] * H / im.shape[0]), H), interpolation=cv2.INTER_CUBIC); x0 = (bg.shape[1] - W) // 2; bg = bg[:, x0:x0 + W]
        bg = cv2.GaussianBlur(bg, (0, 0), 28); bg = (bg * .62).astype(np.uint8)
        card = cv2.resize(im, (1300, int(im.shape[0] * 1300 / im.shape[1])), interpolation=cv2.INTER_LANCZOS4)
        cache[name] = ("card", bg, card)
    else:
        im = cv2.resize(im, (W, int(im.shape[0] * W / im.shape[1])), interpolation=cv2.INTER_CUBIC); cache[name] = ("full", im)
    return cache[name]
def cam_params(cam, u, focus):
    fx, fy = focus
    if cam == "tiltup": return 1 + .25 * u, .5 + (fx - .5) * u, .62 - (.62 - fy) * u
    if cam == "pushin": return 1 + .2 * u, .5 + (fx - .5) * u, .5 + (fy - .5) * u
    if cam == "pullout": return 1.22 - .2 * u, fx + (.5 - fx) * u, fy + (.5 - fy) * u
    if cam == "panright": return 1.15, .38 + .24 * u, fy
    if cam == "panleft": return 1.15, .62 - .24 * u, fy
    return 1.08 + .04 * u, fx, fy   # shake / hold
def view(img, z, cx, cy, ow, oh):   # crop a window of the image (zoom z, centre cx,cy in 0-1) to ow x oh, never past the edges
    ih, iw = img.shape[:2]; vw, vh = iw / z, iw / z * oh / ow
    if vh > ih: vh = ih / 1.0; vw = vh * ow / oh
    x = min(max(cx * iw - vw / 2, 0), iw - vw); y = min(max(cy * ih - vh / 2, 0), ih - vh)
    M = np.float32([[ow / vw, 0, -x * ow / vw], [0, oh / vh, -y * oh / vh]])
    return cv2.warpAffine(img, M, (ow, oh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
font = ImageFont.truetype(FONT, 84); tfont = ImageFont.truetype(FONT, 48); hfont = ImageFont.truetype(FONT, 118)
title, hook = ep["tiktok"]["title"], ep["tiktok"].get("hook", "")
fdir = f"/tmp/ps_{ep['id']}"; os.makedirs(fdir, exist_ok=True)
nfr = int(total * FPS)
for f in range(nfr):
    t = f / FPS; li = max([i for i, l in enumerate(T) if t >= l["start"] - .25] or [0]); L, M = T[li], lines[li]
    t0 = T[li]["start"] - .25; t1 = T[li + 1]["start"] - .25 if li + 1 < len(T) else total; u = ease(min(1, max(0, (t - t0) / max(.5, t1 - t0))))
    z, cx, cy = cam_params(M.get("cam", "pushin"), u, M.get("focus", [.5, .45]))
    sh = 0
    if M.get("cam") == "shake" and t - t0 < .6: k = t - t0; sh = 22 * np.exp(-k * 7) * np.sin(k * 70)
    lay = load(M["panel"], M.get("layout", "full"))
    if lay[0] == "full": fr = view(lay[1], z, cx, cy + sh / 2000, W, H)
    else:
        fr = lay[1].copy(); cw, ch = 1000, 640; card = view(lay[2], z, cx, cy, cw, ch)
        y0 = 560 + int(sh); x0 = (W - cw) // 2
        cv2.rectangle(fr, (x0 - 10, y0 - 10 + 14), (x0 + cw + 10, y0 + ch + 10 + 14), (0, 0, 0), -1)
        fr = cv2.addWeighted(fr, 1, np.zeros_like(fr), 0, 0); cv2.rectangle(fr, (x0 - 10, y0 - 10), (x0 + cw + 10, y0 + ch + 10), (253, 251, 238), -1)
        fr[y0:y0 + ch, x0:x0 + cw] = card
    # cut flash (2 frames white) on a new shot, impact flash on "sfx":"scratch"
    if t - t0 < 2 / FPS and li > 0 and lines[li - 1]["panel"] != M["panel"]: fr = cv2.addWeighted(fr, .55, np.full_like(fr, 255), .45, 0)
    img = Image.fromarray(fr); d = ImageDraw.Draw(img, "RGBA")
    for i in range(24):   # light dust motes
        r = np.random.RandomState(i); y = (r.rand() * H - t * (18 + i % 5 * 7)) % H; x = r.rand() * W + np.sin(t + i) * 8; d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 248, 225, 90))
    d.text((W / 2, 205), title, font=tfont, fill="white", anchor="mm", stroke_width=7, stroke_fill="#1b1b1b")
    d.rounded_rectangle([110, 252, 970, 266], 7, fill=(0, 0, 0, 90)); d.rounded_rectangle([110, 252, 110 + 860 * t / total, 266], 7, fill="#f9d65c")
    if t < 1.5 and hook:   # hook card in the first 1.5 s
        d.rectangle([0, 0, W, H], fill=(10, 8, 30, int(140 * min(1, (1.5 - t) / .3))))
        ws, rows, cur = hook.split(), [], ""
        for w_ in ws: cur = (cur + " " + w_).strip() if len(cur + " " + w_) <= 13 else (rows.append(cur) or w_)
        rows.append(cur)
        for k, r_ in enumerate(rows): d.text((W / 2, 820 + k * 135 - (len(rows) - 1) * 67), r_, font=hfont, fill="#f9d65c" if k % 2 else "white", anchor="mm", stroke_width=12, stroke_fill="#1b1b1b")
    else:   # karaoke caption of the current line, max 2 lines, inside the safe area
        words = L["say"].split(); dur = max(.3, L["end"] - L["start"]); tot = sum(len(w_) + 1 for w_ in words); acc, wi = 0, -1
        for k, w_ in enumerate(words):
            if t >= L["start"] + dur * acc / tot: wi = k
            acc += len(w_) + 1
        if wi >= 0:
            rowsI, cur = [], []
            for k in range(len(words)):
                if cur and len(" ".join(words[j] for j in cur + [k])) > 18: rowsI.append(cur); cur = []
                cur.append(k)
            rowsI.append(cur); ri = next(i for i, r_ in enumerate(rowsI) if wi in r_); show = rowsI[ri - (ri % 2): ri - (ri % 2) + 2]
            for k, idx in enumerate(show):
                txt = " ".join(words[j] for j in idx).upper(); x0 = W / 2 - d.textlength(txt, font=font) / 2; y = 1430 + k * 104 - (len(show) - 1) * 52
                for j in idx:
                    wt = words[j].upper(); d.text((x0, y), wt, font=font, fill="#f9d65c" if j == wi else "white", anchor="ls", stroke_width=11, stroke_fill="#1b1b1b"); x0 += d.textlength(wt + " ", font=font)
    img.save(f"{fdir}/f{f:05d}.jpg", quality=92)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", f"{fdir}/f%05d.jpg",
  "-f", "lavfi", "-i", "color=c=0x808080:s=36x64:r=12,noise=c0s=60:allf=t,lutyuv=y=128+(val-128)*0.03,scale=1080:1920:flags=bicubic,fps=24",
  "-f", "lavfi", "-i", "color=c=0x808080:s=36x64:r=12,noise=c0s=60:allf=t+u,lutyuv=y=128+(val-128)*0.03,scale=1080:1920:flags=bicubic,fps=24",
  "-i", wav, "-filter_complex", "[0:v][1:v][2:v]displace=edge=smear,format=yuv420p[v]", "-map", "[v]", "-map", "3:a",
  "-c:v", "libx264", "-crf", "22", "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
print("done", out, nfr / FPS)
