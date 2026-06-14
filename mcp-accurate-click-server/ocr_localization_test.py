"""
Measure REAL OCR localization error -- the number the whole tool depends on.

Ground truth = the actual rendered INK bounding box of each word (found by
scanning the rasterized pixels), which is exactly what a text detector aims to
box. We then run real PaddleOCR and compare detected box centers to true ink
centers, reporting BOTH:
  (a) raw error, and
  (b) residual scatter AFTER removing the mean offset -- i.e. the part the
      tool's mean-bias calibration can NOT remove. (b) is the honest input
      noise that bounds real-world click accuracy.
"""
import os
os.environ["FLAGS_use_mkldnn"] = "0"  # avoid oneDNN PIR crash on this CPU
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def load_font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

W, H = 1280, 720
words = ["Submit", "Cancel", "File", "Settings", "Search", "Login",
         "Logout", "Profile", "Delete", "Upload", "Download", "Help"]
font = load_font(22)
positions = [(x, y) for y in range(80, H - 80, 130) for x in range(80, W - 200, 300)]

scene = Image.new("RGB", (W, H), "white")
truth = []  # (word, cx, cy) from actual ink pixels
for word, (x, y) in zip(words, positions):
    # render this word alone to get its exact ink bbox, then composite
    tmp = Image.new("L", (W, H), 255)
    ImageDraw.Draw(tmp).text((x, y), word, fill=0, font=font)
    ink = np.argwhere(np.asarray(tmp) < 128)  # (row, col) of black pixels
    (y0, x0), (y1, x1) = ink.min(0), ink.max(0)
    truth.append((word, (x0 + x1) / 2, (y0 + y1) / 2))
    ImageDraw.Draw(scene).text((x, y), word, fill="black", font=font)

img_path = "/tmp/ocr_scene.png"
scene.save(img_path)
print(f"Rendered {len(truth)} words to {img_path} ({W}x{H})")

from paddleocr import PaddleOCR
try:
    ocr = PaddleOCR(lang="en", enable_mkldnn=False)
except Exception:
    ocr = PaddleOCR(lang="en")

dets = []
for res in ocr.predict(img_path):
    d = res if isinstance(res, dict) else getattr(res, "json", {}).get("res", res)
    polys = d.get("rec_polys", d.get("dt_polys", []))
    texts = d.get("rec_texts", [])
    for box, text in zip(polys, texts):
        box = np.array(box)
        dets.append((text, box[:, 0].mean(), box[:, 1].mean()))
print(f"PaddleOCR returned {len(dets)} detections\n")

print(f"{'word':>10} {'dx':>7} {'dy':>7} {'raw_px':>7}")
offs = []
for word, tx, ty in truth:
    best, bd = None, 1e9
    for text, cx, cy in dets:
        dd = ((cx - tx) ** 2 + (cy - ty) ** 2) ** 0.5
        if dd < bd:
            bd, best = dd, (cx, cy)
    if best and bd < 80:
        dx, dy = best[0] - tx, best[1] - ty
        offs.append((dx, dy))
        print(f"{word:>10} {dx:>7.1f} {dy:>7.1f} {bd:>7.1f}")
    else:
        print(f"{word:>10} {'<MISSED>':>7}")

offs = np.array(offs)
raw = np.linalg.norm(offs, axis=1)
mean_off = offs.mean(0)                          # the systematic part calibration removes
residual = np.linalg.norm(offs - mean_off, axis=1)  # the part it can't
print("\n=== REAL PaddleOCR localization vs true ink center (clean image) ===")
print(f"matched:            {len(offs)}/{len(truth)}")
print(f"raw mean err:       {raw.mean():.2f}px  (median {np.median(raw):.2f})")
print(f"systematic offset:  dx={mean_off[0]:.2f}  dy={mean_off[1]:.2f}  (calibration removes this)")
print(f"RESIDUAL scatter:   {residual.mean():.2f}px mean / {residual.max():.2f}px max")
print("  -> residual is what survives mean-bias calibration; it bounds click accuracy.")
