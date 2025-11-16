# Mathematical Solution Specification
## Accurate OCR-to-Click System for Windows

**Version**: 1.0
**Date**: November 2024
**Research Teams**: 100 Researcher Assistants

---

## Table of Contents

1. [Overview](#overview)
2. [Coordinate Space Definitions](#coordinate-space-definitions)
3. [Transformation Pipeline](#transformation-pipeline)
4. [Calibration Mathematics](#calibration-mathematics)
5. [Error Analysis](#error-analysis)
6. [Implementation Algorithms](#implementation-algorithms)
7. [Performance Requirements](#performance-requirements)

---

## Overview

### Problem Statement

Given:
- OCR output coordinates `(x_ocr, y_ocr)` from screenshot
- Target text to click on
- Windows system with arbitrary:
  - DPI scaling (96-240 DPI)
  - Multi-monitor configuration
  - Display orientations

Required:
- Click accuracy within ε = 1 pixel (99% confidence)
- Sub-pixel precision for critical UI elements
- Robustness to OCR errors and system variations

### Solution Architecture

**7-Stage Transformation Pipeline**:

```
Input: OCR bounding box + screenshot metadata
Output: Accurate click at physical pixel location

Pipeline:
1. OCR Normalization: Any format → XYXY physical pixels
2. Center Computation: XYXY → (x_center, y_center)
3. DPI Correction: Handle logical ↔ physical conversion
4. Multi-Monitor Adjustment: Account for virtual desktop offset
5. SendInput Normalization: Physical pixels → [0, 65535] range
6. Calibration: Apply learned correction function
7. Validation: Verify accuracy within threshold
```

---

## Coordinate Space Definitions

### Mathematical Notation

| Symbol | Definition | Domain |
|--------|------------|--------|
| `𝒪` | OCR output space | Depends on OCR engine |
| `𝒫` | Physical pixel space | ℤ² |
| `𝒮` | Screenshot pixel space | {(x,y) : 0 ≤ x < W, 0 ≤ y < H} |
| `𝒱` | Virtual desktop space | ℤ² (multi-monitor) |
| `𝒩` | SendInput normalized space | [0, 65535]² |
| `DPI` | Dots per inch | ℝ⁺, typically {96, 120, 144, 168, 192, 240} |
| `σ` | Scale factor | σ = DPI / 96 |

### Space Relationships

```
OCR Space (𝒪)
    ↓ [Format Normalization]
Screenshot Space (𝒮)
    ↓ [Identity if screenshot = screen]
    ↓ [Scaling if screenshot ≠ screen resolution]
Physical Pixel Space (𝒫)
    ↓ [Virtual Desktop Offset]
Virtual Desktop Space (𝒱)
    ↓ [SendInput Normalization]
Normalized Space (𝒩)
```

### Transformation Functions

#### T₁: OCR Format Normalization

**Input**: OCR bounding box in arbitrary format
**Output**: XYXY format in screenshot space

```
T₁: 𝒪 → 𝒮

T₁(bbox_ocr) = (x_min, y_min, x_max, y_max) where:

If format = XYWH:
    x_min = bbox[0]
    y_min = bbox[1]
    x_max = bbox[0] + bbox[2]
    y_max = bbox[1] + bbox[3]

If format = Quad-4:
    x_min = min(p[0] for p in bbox)
    y_min = min(p[1] for p in bbox)
    x_max = max(p[0] for p in bbox)
    y_max = max(p[1] for p in bbox)

If format = Normalized:
    x_min = bbox[0] × W_screenshot
    y_min = bbox[1] × H_screenshot
    x_max = bbox[2] × W_screenshot
    y_max = bbox[3] × H_screenshot
```

#### T₂: Center Point Computation

**Input**: XYXY bounding box
**Output**: Click target center

```
T₂: ℝ⁴ → ℝ²

T₂(x_min, y_min, x_max, y_max) = (x_c, y_c) where:

Simple average:
    x_c = (x_min + x_max) / 2
    y_c = (y_min + y_max) / 2

Weighted by confidence (if available):
    x_c = Σ(x × conf(x,y)) / Σconf(x,y)  for (x,y) ∈ bbox
    y_c = Σ(y × conf(x,y)) / Σconf(x,y)  for (x,y) ∈ bbox
```

#### T₃: Screenshot-to-Screen Scaling

**Input**: Coordinates in screenshot space
**Output**: Coordinates in physical pixel space

```
T₃: 𝒮 → 𝒫

T₃(x_s, y_s) = (x_p, y_p) where:

If screenshot dimensions = screen dimensions:
    (x_p, y_p) = (x_s, y_s)  [Identity]

If screenshot is scaled:
    scale_x = W_screen / W_screenshot
    scale_y = H_screen / H_screenshot

    x_p = x_s × scale_x
    y_p = y_s × scale_y

Note: For maximum accuracy, always capture screenshots at native resolution
```

#### T₄: DPI Awareness Correction

**Input**: Physical or logical pixels (depending on DPI awareness mode)
**Output**: Physical pixels (for multi-monitor consistency)

```
T₄: 𝒫 or DIPs → 𝒫

If application is DPI-unaware:
    # System has already scaled, coordinates are logical
    dpi = GetDpiForMonitor(monitor_at_point(x, y))
    x_p = x_logical × (dpi / 96)
    y_p = y_logical × (dpi / 96)

If application is Per-Monitor DPI Aware V2:
    # Coordinates are already physical
    (x_p, y_p) = (x, y)  [Identity]
```

#### T₅: Virtual Desktop Offset

**Input**: Physical pixels in monitor-local coordinates
**Output**: Physical pixels in virtual desktop coordinates

```
T₅: 𝒫 → 𝒱

V_left = GetSystemMetrics(SM_XVIRTUALSCREEN)
V_top = GetSystemMetrics(SM_YVIRTUALSCREEN)

T₅(x_p, y_p) = (x_v, y_v) where:
    x_v = x_p - V_left
    y_v = y_p - V_top

Note: V_left and V_top can be negative if monitors are positioned
      left of or above the primary monitor
```

#### T₆: SendInput Normalization

**Input**: Virtual desktop coordinates
**Output**: SendInput normalized coordinates [0, 65535]

```
T₆: 𝒱 → 𝒩

V_width = GetSystemMetrics(SM_CXVIRTUALSCREEN)
V_height = GetSystemMetrics(SM_CYVIRTUALSCREEN)

T₆(x_v, y_v) = (x_n, y_n) where:
    x_n = ⌊(x_v × 65535) / V_width⌋
    y_n = ⌊(y_v × 65535) / V_height⌋

    # Clamp to valid range
    x_n = max(0, min(65535, x_n))
    y_n = max(0, min(65535, y_n))

Note: Use integer division to avoid floating-point rounding errors
```

#### T₇: Calibration Correction

**Input**: Uncorrected coordinates
**Output**: Corrected coordinates

```
T₇: ℝ² → ℝ²

Homography model:
    [x']   [h₁₁  h₁₂  h₁₃]   [x]
    [y'] = [h₂₁  h₂₂  h₂₃] × [y]
    [w ]   [h₃₁  h₃₂  h₃₃]   [1]

    x_corrected = x' / w
    y_corrected = y' / w

Polynomial model (degree 2):
    Δx = a₁x + a₂y + a₃x² + a₄xy + a₅y²
    Δy = b₁x + b₂y + b₃x² + b₄xy + b₅y²

    x_corrected = x + Δx
    y_corrected = y + Δy

Radial distortion model:
    r = √(x² + y²)
    Δr = k₁r³ + k₂r⁵

    x_corrected = x + Δr × (x / r)
    y_corrected = y + Δr × (y / r)
```

---

## Transformation Pipeline

### Complete Pipeline Function

```python
def ocr_to_click_coordinates(
    bbox_ocr,              # OCR bounding box (any format)
    ocr_format,            # Format type string
    screenshot_size,       # (width, height) of screenshot
    screen_size,           # (width, height) of physical screen
    calibration_matrix=None  # Optional 3×3 homography
) -> tuple[int, int]:
    """
    Complete transformation pipeline: OCR → Physical Click Coordinates

    Returns:
        (x_physical, y_physical) - coordinates for SendInput
    """
    # Stage 1: Normalize OCR format to XYXY
    x_min, y_min, x_max, y_max = normalize_ocr_format(
        bbox_ocr, ocr_format, screenshot_size[0], screenshot_size[1]
    )

    # Stage 2: Compute center point
    x_center = (x_min + x_max) / 2
    y_center = (y_min + y_max) / 2

    # Stage 3: Scale from screenshot to screen
    if screenshot_size != screen_size:
        scale_x = screen_size[0] / screenshot_size[0]
        scale_y = screen_size[1] / screenshot_size[1]
        x_center *= scale_x
        y_center *= scale_y

    # Stage 4: DPI correction (assuming Per-Monitor V2)
    # Already in physical pixels, no correction needed

    # Stage 5: Multi-monitor offset
    # Will be handled in SendInput normalization

    # Stage 6: Apply calibration if available
    if calibration_matrix is not None:
        x_center, y_center = apply_homography(
            np.array([[x_center, y_center]]),
            calibration_matrix
        )[0]

    # Return as physical pixels (integer)
    return int(round(x_center)), int(round(y_center))
```

### SendInput Implementation

```python
def accurate_click(x_physical, y_physical):
    """
    Execute accurate click using SendInput

    Args:
        x_physical, y_physical: Physical pixel coordinates

    Returns:
        True if successful
    """
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    # Get virtual desktop bounds
    v_left = user32.GetSystemMetrics(76)    # SM_XVIRTUALSCREEN
    v_top = user32.GetSystemMetrics(77)     # SM_YVIRTUALSCREEN
    v_width = user32.GetSystemMetrics(78)   # SM_CXVIRTUALSCREEN
    v_height = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN

    # Adjust for virtual desktop offset
    x_adjusted = x_physical - v_left
    y_adjusted = y_physical - v_top

    # Normalize to [0, 65535]
    x_normalized = (x_adjusted * 65535) // v_width
    y_normalized = (y_adjusted * 65535) // v_height

    # Clamp to valid range
    x_normalized = max(0, min(65535, x_normalized))
    y_normalized = max(0, min(65535, y_normalized))

    # Define input structures
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ('dx', wintypes.LONG),
            ('dy', wintypes.LONG),
            ('mouseData', wintypes.DWORD),
            ('dwFlags', wintypes.DWORD),
            ('time', wintypes.DWORD),
            ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))
        ]

    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = [('mi', MOUSEINPUT)]
        _anonymous_ = ('_input',)
        _fields_ = [
            ('type', wintypes.DWORD),
            ('_input', _INPUT)
        ]

    # Constants
    INPUT_MOUSE = 0
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_ABSOLUTE = 0x8000
    MOUSEEVENTF_VIRTUALDESK = 0x4000

    # Create events
    events = []

    # Event 1: Move
    move = INPUT()
    move.type = INPUT_MOUSE
    move.mi.dx = x_normalized
    move.mi.dy = y_normalized
    move.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
    events.append(move)

    # Event 2: Down
    down = INPUT()
    down.type = INPUT_MOUSE
    down.mi.dx = x_normalized
    down.mi.dy = y_normalized
    down.mi.dwFlags = MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
    events.append(down)

    # Event 3: Up
    up = INPUT()
    up.type = INPUT_MOUSE
    up.mi.dx = x_normalized
    up.mi.dy = y_normalized
    up.mi.dwFlags = MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
    events.append(up)

    # Send inputs
    inputs_array = (INPUT * 3)(*events)
    result = user32.SendInput(3, inputs_array, ctypes.sizeof(INPUT))

    return result == 3
```

---

## Calibration Mathematics

### Homography Estimation

#### Direct Linear Transform (DLT)

Given N ≥ 4 point correspondences:
- Source points (OCR): {(x₁, y₁), (x₂, y₂), ..., (xₙ, yₙ)}
- Destination points (actual): {(x'₁, y'₁), (x'₂, y'₂), ..., (x'ₙ, y'ₙ)}

Find homography matrix H:
```
[x'ᵢ]   [h₁₁  h₁₂  h₁₃]   [xᵢ]
[y'ᵢ] = [h₂₁  h₂₂  h₂₃] × [yᵢ]
[w'ᵢ]   [h₃₁  h₃₂  h₃₃]   [1 ]

where: x'ᵢ/w'ᵢ = x'ᵢ_final, y'ᵢ/w'ᵢ = y'ᵢ_final
```

**Linear System Construction**:

For each correspondence i, create two equations:
```
h₁₁xᵢ + h₁₂yᵢ + h₁₃ - h₃₁xᵢx'ᵢ - h₃₂yᵢx'ᵢ - h₃₃x'ᵢ = 0
h₂₁xᵢ + h₂₂yᵢ + h₂₃ - h₃₁xᵢy'ᵢ - h₃₂yᵢy'ᵢ - h₃₃y'ᵢ = 0
```

Matrix form: **Ah = 0**

```
A = [-x₁  -y₁  -1   0    0   0   x₁x'₁  y₁x'₁  x'₁]
    [ 0    0   0  -x₁  -y₁ -1   x₁y'₁  y₁y'₁  y'₁]
    [-x₂  -y₂  -1   0    0   0   x₂x'₂  y₂x'₂  x'₂]
    [ 0    0   0  -x₂  -y₂ -1   x₂y'₂  y₂y'₂  y'₂]
    [  ...                                        ]

h = [h₁₁, h₁₂, h₁₃, h₂₁, h₂₂, h₂₃, h₃₁, h₃₂, h₃₃]ᵀ
```

**Solution via SVD**:
```
A = U Σ Vᵀ
h = last column of V (corresponding to smallest singular value)
H = reshape(h, [3, 3])
H = H / H[2,2]  # Normalize
```

#### Levenberg-Marquardt Refinement

After initial DLT estimate, refine using non-linear optimization:

**Cost Function**:
```
E(h) = Σᵢ ||x'ᵢ - H(h)xᵢ||²

where H(h)xᵢ denotes the projected point:
    [u]       [xᵢ]
    [v] = H × [yᵢ]
    [w]       [1 ]

    projected = (u/w, v/w)
```

**Levenberg-Marquardt Update**:
```
h_{k+1} = h_k - (Jᵀ J + λI)⁻¹ Jᵀ r

where:
    J = Jacobian matrix of residuals
    r = residual vector
    λ = damping parameter (adjusted each iteration)
```

### RANSAC for Robust Estimation

When correspondences contain outliers (OCR errors), use RANSAC:

**Algorithm**:
```
Input:
    - Point correspondences: {(sᵢ, dᵢ)}ᵢ₌₁ⁿ
    - Inlier threshold: τ (e.g., 5 pixels)
    - Number of iterations: K (e.g., 1000)
    - Minimum inliers: M (e.g., 10)

Output:
    - Best homography H_best
    - Inlier mask

Procedure:
    H_best ← None
    max_inliers ← 0

    for k = 1 to K:
        # Sample minimal set (4 correspondences)
        sample ← random_sample({(sᵢ, dᵢ)}, 4)

        # Compute homography
        H ← DLT(sample)

        # Count inliers
        inliers ← 0
        for i = 1 to n:
            projected ← H × sᵢ
            error ← ||dᵢ - projected||₂

            if error < τ:
                inliers ← inliers + 1

        if inliers > max_inliers:
            max_inliers ← inliers
            H_best ← H

    # Refine using all inliers
    if max_inliers ≥ M:
        inlier_set ← {(sᵢ, dᵢ) | ||dᵢ - H_best × sᵢ|| < τ}
        H_best ← LM_refinement(DLT(inlier_set), inlier_set)

    return H_best
```

**Iteration Count Calculation**:

Probability of success:
```
P(success) = 1 - (1 - (1 - ε)ˢ)ᴷ

where:
    ε = outlier ratio (e.g., 0.3 = 30% outliers)
    s = sample size (4 for homography)
    K = iterations

For P(success) = 0.99, ε = 0.3:
    K = log(1 - 0.99) / log(1 - (1 - 0.3)⁴)
    K ≈ 72 iterations

Conservative: K = 1000 gives >99.99% success
```

### Polynomial Correction Model

For simple distortions, polynomial model may suffice:

**Second-Order Model**:
```
Δx(x, y) = a₀ + a₁x + a₂y + a₃x² + a₄xy + a₅y²
Δy(x, y) = b₀ + b₁x + b₂y + b₃x² + b₄xy + b₅y²

Corrected coordinates:
    x_corrected = x + Δx(x, y)
    y_corrected = y + Δy(x, y)
```

**Least Squares Fitting**:

Given N correspondences {(xᵢ, yᵢ) → (x'ᵢ, y'ᵢ)}:

```
Compute deltas:
    Δxᵢ = x'ᵢ - xᵢ
    Δyᵢ = y'ᵢ - yᵢ

Feature matrix (N × 6):
    Φ = [1  x₁  y₁  x₁²  x₁y₁  y₁²]
        [1  x₂  y₂  x₂²  x₂y₂  y₂²]
        [⋮   ⋮   ⋮   ⋮    ⋮     ⋮ ]
        [1  xₙ  yₙ  xₙ²  xₙyₙ  yₙ²]

Solve normal equations:
    a = (ΦᵀΦ)⁻¹Φᵀ Δx
    b = (ΦᵀΦ)⁻¹Φᵀ Δy

where:
    a = [a₀, a₁, a₂, a₃, a₄, a₅]ᵀ
    b = [b₀, b₁, b₂, b₃, b₄, b₅]ᵀ
```

**Regularization** (to prevent overfitting):

Ridge regression:
```
a = (ΦᵀΦ + λI)⁻¹Φᵀ Δx
b = (ΦᵀΦ + λI)⁻¹Φᵀ Δy

where λ > 0 is regularization parameter (e.g., λ = 0.01)
```

---

## Error Analysis

### Sources of Error

1. **OCR Localization Error**: ±2-5 pixels (typical)
2. **Screenshot Scaling Error**: ±0-1 pixel (if resized)
3. **DPI Rounding Error**: ±0.5 pixels (floating point)
4. **SendInput Quantization**: ±0-1 pixel (65535 resolution)
5. **System Latency**: 0-16 ms (can cause missed targets on moving UI)

### Error Propagation

**Gaussian Error Propagation**:

If input has error σᵢₙ, output error through function f:
```
σₒᵤₜ² = Σᵢ (∂f/∂xᵢ)² σᵢₙ,ᵢ²

For linear scaling: f(x) = ax
    σₒᵤₜ = |a| σᵢₙ

For addition: f(x, y) = x + y
    σₒᵤₜ = √(σₓ² + σᵧ²)
```

**Example**: Click accuracy through pipeline

Assume:
- OCR error: σ_ocr = 3 pixels
- Screenshot scaling: scale = 1.5, σ_scale = 0
- DPI correction: no error in Per-Monitor V2
- SendInput quantization: σ_quant = 0.5 pixels

Total error:
```
σ_total = √((1.5 × 3)² + 0.5²)
        = √(20.25 + 0.25)
        = √20.5
        ≈ 4.5 pixels
```

**With Calibration**:

If calibration reduces systematic error:
```
σ_calibrated = √(σ_random² + σ_calibration²)

If calibration has 1-pixel residual error:
    σ_total = √(3² + 1² + 0.5²)
            = √10.25
            ≈ 3.2 pixels

Improvement: 4.5 → 3.2 pixels (29% reduction)
```

### Confidence Intervals

For N measurements with mean μ and standard deviation σ:

**95% Confidence Interval**:
```
CI = μ ± t_{α/2, N-1} × (σ / √N)

For N = 30, α = 0.05:
    t_{0.025, 29} ≈ 2.045

Example:
    Mean error: μ = 2.5 pixels
    Std dev: σ = 1.2 pixels
    N = 30 measurements

    CI = 2.5 ± 2.045 × (1.2 / √30)
       = 2.5 ± 0.45
       = [2.05, 2.95] pixels
```

---

## Implementation Algorithms

### Complete OCR-to-Click System

```python
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, List
import ctypes
from ctypes import wintypes

@dataclass
class ClickTarget:
    """Represents a click target with coordinates and metadata"""
    text: str
    x: float
    y: float
    confidence: float
    bbox: Tuple[float, float, float, float]  # XYXY format

class AccurateClickSystem:
    """
    Complete accurate click system with calibration
    """

    def __init__(self, use_calibration=True):
        """Initialize the click system"""
        self.use_calibration = use_calibration
        self.calibration_matrix = None
        self._init_dpi_awareness()

    def _init_dpi_awareness(self):
        """Set Per-Monitor DPI Awareness V2"""
        try:
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
            ctypes.windll.user32.SetProcessDpiAwarenessContext(
                DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            )
        except:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:
                ctypes.windll.user32.SetProcessDPIAware()

    def calibrate(self, calibration_points: List[Tuple[Tuple[float, float], Tuple[float, float]]]):
        """
        Calibrate system using known point correspondences

        Args:
            calibration_points: List of (ocr_point, actual_point) tuples
        """
        if len(calibration_points) < 4:
            raise ValueError("Need at least 4 calibration points")

        src_points = np.array([p[0] for p in calibration_points])
        dst_points = np.array([p[1] for p in calibration_points])

        # Use RANSAC for robustness
        self.calibration_matrix, inliers = self._ransac_homography(
            src_points, dst_points, threshold=5.0, iterations=1000
        )

        inlier_ratio = np.sum(inliers) / len(inliers)
        print(f"Calibration complete: {np.sum(inliers)}/{len(inliers)} inliers ({inlier_ratio:.1%})")

    def _ransac_homography(self, src_pts, dst_pts, threshold, iterations):
        """RANSAC homography estimation"""
        n = len(src_pts)
        best_H = None
        best_inliers = np.zeros(n, dtype=bool)
        best_count = 0

        for _ in range(iterations):
            # Sample 4 points
            indices = np.random.choice(n, 4, replace=False)
            sample_src = src_pts[indices]
            sample_dst = dst_pts[indices]

            try:
                H = self._compute_homography_dlt(sample_src, sample_dst)

                # Count inliers
                projected = self._apply_homography(src_pts, H)
                errors = np.linalg.norm(dst_pts - projected, axis=1)
                inliers = errors < threshold
                count = np.sum(inliers)

                if count > best_count:
                    best_count = count
                    best_inliers = inliers
                    best_H = H
            except:
                continue

        # Refine with all inliers
        if best_count >= 4:
            inlier_src = src_pts[best_inliers]
            inlier_dst = dst_pts[best_inliers]
            best_H = self._compute_homography_dlt(inlier_src, inlier_dst)

        return best_H, best_inliers

    def _compute_homography_dlt(self, src, dst):
        """Direct Linear Transform for homography"""
        n = len(src)
        A = []

        for i in range(n):
            x, y = src[i]
            xp, yp = dst[i]

            A.append([-x, -y, -1, 0, 0, 0, xp*x, xp*y, xp])
            A.append([0, 0, 0, -x, -y, -1, yp*x, yp*y, yp])

        A = np.array(A)
        U, S, Vt = np.linalg.svd(A)
        H = Vt[-1].reshape(3, 3)
        H = H / H[2, 2]

        return H

    def _apply_homography(self, points, H):
        """Apply homography to points"""
        points_h = np.hstack([points, np.ones((len(points), 1))])
        transformed_h = (H @ points_h.T).T
        transformed = transformed_h[:, :2] / transformed_h[:, 2:3]
        return transformed

    def click(self, x: float, y: float) -> bool:
        """
        Perform accurate click at coordinates

        Args:
            x, y: Physical pixel coordinates

        Returns:
            True if successful
        """
        # Apply calibration if available
        if self.use_calibration and self.calibration_matrix is not None:
            corrected = self._apply_homography(
                np.array([[x, y]]),
                self.calibration_matrix
            )[0]
            x, y = corrected[0], corrected[1]

        # Convert to integers
        x = int(round(x))
        y = int(round(y))

        # Execute click
        return self._send_input_click(x, y)

    def _send_input_click(self, x_phys, y_phys):
        """Low-level SendInput click"""
        user32 = ctypes.windll.user32

        # Virtual desktop bounds
        v_left = user32.GetSystemMetrics(76)
        v_top = user32.GetSystemMetrics(77)
        v_width = user32.GetSystemMetrics(78)
        v_height = user32.GetSystemMetrics(79)

        # Normalize
        x_adj = x_phys - v_left
        y_adj = y_phys - v_top
        x_norm = (x_adj * 65535) // v_width
        y_norm = (y_adj * 65535) // v_height
        x_norm = max(0, min(65535, x_norm))
        y_norm = max(0, min(65535, y_norm))

        # Define structures
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ('dx', wintypes.LONG),
                ('dy', wintypes.LONG),
                ('mouseData', wintypes.DWORD),
                ('dwFlags', wintypes.DWORD),
                ('time', wintypes.DWORD),
                ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))
            ]

        class INPUT(ctypes.Structure):
            class _INPUT(ctypes.Union):
                _fields_ = [('mi', MOUSEINPUT)]
            _anonymous_ = ('_input',)
            _fields_ = [
                ('type', wintypes.DWORD),
                ('_input', _INPUT)
            ]

        # Create events
        events = []
        for flag in [0x0001 | 0x8000 | 0x4000,  # MOVE | ABSOLUTE | VIRTUALDESK
                     0x0002 | 0x8000 | 0x4000,  # LEFTDOWN | ABSOLUTE | VIRTUALDESK
                     0x0004 | 0x8000 | 0x4000]: # LEFTUP | ABSOLUTE | VIRTUALDESK
            inp = INPUT()
            inp.type = 0  # INPUT_MOUSE
            inp.mi.dx = x_norm
            inp.mi.dy = y_norm
            inp.mi.dwFlags = flag
            events.append(inp)

        # Send
        inputs = (INPUT * 3)(*events)
        result = user32.SendInput(3, inputs, ctypes.sizeof(INPUT))

        return result == 3
```

---

## Performance Requirements

### Accuracy Targets

| Metric | Minimum | Target | Ideal |
|--------|---------|--------|-------|
| Mean Error | <5px | <2px | <1px |
| Median Error | <3px | <1px | <0.5px |
| 95th Percentile | <10px | <5px | <2px |
| Success Rate (±2px) | >90% | >95% | >99% |
| Calibration Time | <60s | <30s | <10s |
| Click Latency | <100ms | <50ms | <20ms |

### Computational Complexity

| Operation | Complexity | Typical Time |
|-----------|------------|--------------|
| OCR Extraction | O(WH) | 100-500ms |
| Coordinate Normalization | O(1) | <1ms |
| Homography Application | O(1) | <1ms |
| SendInput | O(1) | <10ms |
| **Total Per Click** | O(WH) | **100-500ms** |
| Calibration (N points) | O(N²K) | 1-30s |

Where:
- W, H = screenshot dimensions
- N = calibration points
- K = RANSAC iterations

---

*This mathematical specification provides the complete theoretical foundation for implementing an accurate OCR-to-click system on Windows with sub-pixel precision.*
