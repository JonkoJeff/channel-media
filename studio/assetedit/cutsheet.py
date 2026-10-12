"""Cut a cream-paper sprite sheet into transparent PNGs by silhouette (flood the paper colour from the border).
python3 cutsheet.py sheet.png PREFIX outdir  -> outdir/PREFIX01.png ... + outdir/_contact.jpg (numbered). Poses with a baked scene (filled rectangle) are skipped."""
import sys, os, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
src, pre, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
im = Image.open(src).convert("RGB"); a = np.asarray(im).astype(int)
paper = np.median(np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)]), 0)
fg = np.abs(a - paper).sum(2) > 38
fg = nd.binary_opening(fg, iterations=1)
grp = nd.binary_dilation(fg, iterations=2)
lab, n = nd.label(grp); H, W = fg.shape; items = []
for i, sl in enumerate(nd.find_objects(lab), 1):
    m = (lab[sl] == i) & fg[sl]; h, w = m.shape
    if m.sum() < 0.0012 * H * W or h < 0.05 * H: continue  # labels / specks
    fill = m.sum() / (h * w)
    if fill > 0.80 and h > 0.07 * H and w > 0.07 * W: continue  # baked scene rectangle
    items.append((sl[0].start // (0.12 * H) , sl[1].start, sl, m))
items.sort(key=lambda t: (round(t[2][0].start / (0.11 * H)), t[1]))
ct = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(ct); rows = []
for k, (_, _, sl, m) in enumerate(items, 1):
    full = np.zeros(fg.shape, bool); full[sl] = m
    full = nd.binary_fill_holes(nd.binary_closing(full, iterations=2))
    ys, xs = np.where(full); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([a[y0:y1, x0:x1].astype(np.uint8), (full[y0:y1, x0:x1] * 255).astype(np.uint8)])
    al = Image.fromarray(rgba[:, :, 3]).filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(0.8)); sp = Image.fromarray(rgba); sp.putalpha(al)
    sp.save(f"{out}/{pre}{k:02d}.png"); ct.paste(sp, (x0, y0), sp); d.text((x0, y0), f"{k}", fill="red")
ct.convert("RGB").save(f"{out}/_contact.jpg", quality=80); print(pre, len(items), "poses")
