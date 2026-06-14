"""
Measure REAL OCR localization error -- the number the whole tool depends on.

We render known words at known pixel centers onto a clean white image, run real
PaddleOCR, match each detection back to the nearest ground-truth word, and report
the pixel distance between the detected box center and the true center.

This is the honest input to the calibration: if this error is ~0.25px the tool's
claims hold; if it's several px, the advertised 99.6%/0.24px is unreachable.
"""
import os
os.environ["FLAGS_use_mkldnn"] = "0"  # avoid oneDNN PIR crash on this CPU
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont

def load_font(size):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

W, H = 1280, 720
words = ["Submit", "Cancel", "File", "Settings", "Search", "Login",
         "Logout", "Profile", "Delete", "Upload", "Download", "Help"]
font = load_font(22)

img = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(img)
truth = []  # (word, cx, cy)
rng = np.random.default_rng(1)
positions = [(x, y) for y in range(80, H - 80, 130) for x in range(80, W - 200, 260)]
for word, (x, y) in zip(words, positions):
    bbox = draw.textbbox((x, y), word, font=font)
    draw.text((x, y), word, fill="black", font=font)
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    truth.append((word, cx, cy))

img_path = "/tmp/ocr_scene.png"
img.save(img_path)
print(f"Rendered {len(truth)} words to {img_path} ({W}x{H})")

from paddleocr import PaddleOCR

dets = []
try:
    # PaddleOCR 3.x API; disable mkldnn to dodge the oneDNN CPU crash
    try:
        ocr = PaddleOCR(lang="en", enable_mkldnn=False)
    except Exception:
        ocr = PaddleOCR(lang="en")
    results = ocr.predict(img_path)
    for res in results:
        d = res if isinstance(res, dict) else getattr(res, "json", {}).get("res", res)
        polys = d.get("rec_polys", d.get("dt_polys", []))
        texts = d.get("rec_texts", [])
        scores = d.get("rec_scores", [1.0] * len(texts))
        for box, text, conf in zip(polys, texts, scores):
            box = np.array(box)
            dets.append((text, box[:, 0].mean(), box[:, 1].mean(), conf))
except Exception:
    # PaddleOCR 2.x fallback
    ocr = PaddleOCR(use_angle_cls=True, lang="en")
    result = ocr.ocr(img_path, cls=True)
    for line in (result[0] or []):
        box, (text, conf) = line
        box = np.array(box)
        dets.append((text, box[:, 0].mean(), box[:, 1].mean(), conf))

print(f"PaddleOCR returned {len(dets)} detections\n")
print(f"{'truth':>10} {'detected':>10} {'true_xy':>14} {'det_xy':>14} {'err_px':>8}")
errs = []
for word, tx, ty in truth:
    best, bd = None, 1e9
    for text, cx, cy, conf in dets:
        d = ((cx - tx) ** 2 + (cy - ty) ** 2) ** 0.5
        if d < bd:
            bd, best = d, (text, cx, cy)
    if best and bd < 60:
        errs.append(bd)
        print(f"{word:>10} {best[0]:>10} ({tx:6.1f},{ty:6.1f}) ({best[1]:6.1f},{best[2]:6.1f}) {bd:8.2f}")
    else:
        print(f"{word:>10} {'<MISSED>':>10}")

errs = np.array(errs)
print("\n=== REAL OCR localization error (clean, ideal conditions) ===")
print(f"matched: {len(errs)}/{len(truth)}")
if len(errs):
    print(f"mean: {errs.mean():.2f}px  median: {np.median(errs):.2f}px  max: {errs.max():.2f}px")
