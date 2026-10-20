"""Cut character poses out of an owner pose sheet (cream background) into transparent PNGs.
Usage: python3 sprites.py sheet.png outdir prefix  -> outdir/prefix_NN.png (reading order) + outdir/prefix_index.jpg (numbered contact sheet)
Grid/separator lines are found from their grey colour; numbers and name labels are dropped by size."""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as nd
src, out, pre = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
im = Image.open(src).convert("RGB"); A = np.asarray(im); a = A.astype(np.float32) / 255
mx, mn = a.max(2), a.min(2); sat = np.where(mx > 0, (mx - mn) / (mx + 1e-6), 0)
grey = (mx > .35) & (mx < .85) & (sat < .12)
ink = ((mx < .42) | (sat > .22))
H, W = mx.shape
def cuts(prof, thr):   # centre positions of runs where prof > thr
    on = prof > thr; out, i = [], 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]: j += 1
            out.append((i + j) // 2); i = j
        else: i += 1
    return out
hs = [0] + cuts(grey.mean(1), .45) + [H]
cells = []
for y0, y1 in zip(hs, hs[1:]):
    if y1 - y0 < 120: continue
    vs = [0] + cuts(grey[y0:y1].mean(0), .5) + [W]
    for x0, x1 in zip(vs, vs[1:]):
        if x1 - x0 > 100: cells.append((y0 + 3, y1 - 3, x0 + 3, x1 - 3))
sprites = []
for y0, y1, x0, x1 in cells:
    m = ink[y0:y1, x0:x1] & ~nd.binary_dilation(grey[y0:y1, x0:x1] & ~ink[y0:y1, x0:x1], iterations=0) if False else ink[y0:y1, x0:x1]
    lab, n = nd.label(nd.binary_dilation(m, iterations=7))
    for k, sl in enumerate(nd.find_objects(lab), 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if h < 90 or (lab[sl] == k).sum() < 6000 or w > 3 * h: continue   # numbers, labels, underlines
        comp = (lab == k) & m
        body = nd.binary_fill_holes(nd.binary_dilation(nd.binary_fill_holes(comp), iterations=2))
        ys, xs = np.where(body); by0, by1, bx0, bx1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        rgba = np.dstack([A[y0:y1, x0:x1][by0:by1, bx0:bx1], (body[by0:by1, bx0:bx1] * 255).astype(np.uint8)])
        sp = Image.fromarray(rgba, "RGBA"); sp.putalpha(sp.getchannel("A").filter(ImageFilter.GaussianBlur(.8)))
        sprites.append((y0 + by0, x0 + bx0, sp))
sprites.sort(key=lambda s: (s[0] // 150, s[1]))
for j, (_, _, sp) in enumerate(sprites, 1): sp.save(f"{out}/{pre}_{j:02d}.png")
T = 160; cols = 8; sheet = Image.new("RGB", (T * cols, T * ((len(sprites) + cols - 1) // cols)), (60, 60, 70)); d = ImageDraw.Draw(sheet)
for j, (_, _, t) in enumerate(sprites):
    t2 = t.copy(); t2.thumbnail((T - 10, T - 22)); x, y = (j % cols) * T, (j // cols) * T
    sheet.paste(t2, (x + 5, y + 18), t2); d.text((x + 4, y + 2), f"{j + 1:02d}", fill=(255, 230, 80))
sheet.save(f"{out}/{pre}_index.jpg"); print(pre, len(cells), "cells", len(sprites), "poses")
