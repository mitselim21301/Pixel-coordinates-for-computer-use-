"""
Honest end-to-end test of the REAL calibration code (no mocks).

Goal: find out what the headline '99.8-100% accuracy / 0.24px error' actually
depends on. We run the project's own SimpleCalibration / RegionalCalibration
against synthetic data with a *known* systematic bias plus varying amounts of
random noise -- the noise stands in for real OCR jitter.
"""
import sys, numpy as np
sys.path.insert(0, "src")
from calibration import SimpleCalibration, RegionalCalibration

rng = np.random.default_rng(0)
W, H = 1920, 1080

def make_data(n, noise_px, bias=(7.0, -4.0)):
    """true points uniformly on screen; measured = true + constant bias + N(0,noise)."""
    true = rng.uniform([0, 0], [W, H], size=(n, 2))
    measured = true + np.array(bias) + rng.normal(0, noise_px, size=(n, 2))
    return measured, true

def evaluate(cal, measured, true):
    corrected = np.array([cal.correct(m) for m in measured])
    err = np.linalg.norm(corrected - true, axis=1)
    within2 = float(np.mean(err <= 2.0)) * 100
    return err.mean(), within2

print(f"{'noise(px)':>10} | {'Simple mean_err':>15} {'<=2px %':>9} | {'Regional mean_err':>17} {'<=2px %':>9}")
print("-" * 78)
for noise in [0.1, 0.3, 0.5, 1.0, 2.0, 4.0, 8.0]:
    # train/test split so we measure generalization, not fit-to-self
    m_tr, t_tr = make_data(200, noise)
    m_te, t_te = make_data(2000, noise)

    s = SimpleCalibration(W, H); s.calibrate(m_tr, t_tr)
    s_err, s_acc = evaluate(s, m_te, t_te)

    r = RegionalCalibration(grid_size=(2, 2), screen_width=W, screen_height=H)
    r.calibrate(m_tr, t_tr)
    r_err, r_acc = evaluate(r, m_te, t_te)

    print(f"{noise:>10.1f} | {s_err:>15.3f} {s_acc:>8.1f}% | {r_err:>17.3f} {r_acc:>8.1f}%")

print()
print("Reference: published PaddleOCR text-detection box error is typically")
print("~1-5 px on clean text and much worse on small/blurry/rotated text.")
