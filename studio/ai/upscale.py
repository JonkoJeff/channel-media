"""Sharpen + enlarge sprites 4x with Real-ESRGAN anime 6B (open source, runs in GitHub Actions on CPU).
Keeps the approved art: no redraw. Alpha is upscaled separately (Lanczos, then re-hardened).
Input: every PNG in the folders given as args. Output: studio/ai/upscaled/<folder name>/<file>."""
import os, sys, numpy as np, torch
from PIL import Image, ImageFilter
from spandrel import ModelLoader
import traceback
try: m = ModelLoader().load_from_file("anime6B.pth").eval()
except Exception: print("::error::load " + traceback.format_exc()[-600:].replace("\n", " | ")); raise
def up(src, dst, f):
        im = Image.open(os.path.join(src, f)).convert("RGBA"); a = im.getchannel("A")
        rgb = Image.new("RGB", im.size, (128, 128, 128)); rgb.paste(im, mask=a)
        x = torch.from_numpy(np.asarray(rgb, dtype=np.float32) / 255).permute(2, 0, 1)[None]
        with torch.no_grad(): y = m(x)[0].clamp(0, 1).permute(1, 2, 0).numpy()
        out = Image.fromarray((y * 255).round().astype(np.uint8))
        al = a.resize(out.size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(1)).point(lambda v: 0 if v < 40 else 255 if v > 215 else int((v - 40) * 255 / 175))
        out.putalpha(al); out.save(os.path.join(dst, f)); print("ok", dst, f, out.size)

for src in sys.argv[1:]:
    dst = os.path.join("studio/ai/upscaled", os.path.basename(os.path.dirname(src.rstrip("/"))) + "_" + os.path.basename(src.rstrip("/")))
    os.makedirs(dst, exist_ok=True)
    for f in sorted(os.listdir(src)):
        if not f.endswith(".png") or os.path.exists(os.path.join(dst, f)): continue
        try: up(src, dst, f)
        except Exception: print(f"::error::{f} " + traceback.format_exc()[-600:].replace("\n", " | ")); raise

