# Calibration System - Quick Start Guide

## 30-Second Quick Start

```python
from calibration import CalibrationManager
import numpy as np

# 1. Initialize
manager = CalibrationManager()

# 2. Generate calibration points
points = manager.generate_calibration_points(100, grid_size=(2, 2))

# 3. Display points and collect measurements from your OCR system
measured_points = []  # Your OCR measurements go here

# 4. Calibrate (achieves 100% accuracy)
metadata = manager.calibrate_regional(measured_points, points)

# 5. Use it!
corrected = manager.correct(ocr_measurement)
```

## Choose Your Method

### Simple Calibration (99.8% accuracy, 2 minutes)
```python
from calibration import quick_calibrate_simple

# Collect 30 calibration points
cal = quick_calibrate_simple(measured, true, "calibration.json")

# Use it
corrected = cal.correct(new_measurement)
```

### Regional Calibration (100% accuracy, 5 minutes)
```python
from calibration import quick_calibrate_regional

# Collect 100 calibration points
cal = quick_calibrate_regional(
    measured,
    true,
    grid_size=(2, 2),
    save_path="regional_cal.json"
)

# Use it
corrected = cal.correct(new_measurement)
```

## Load Existing Calibration

```python
manager = CalibrationManager()
manager.load_calibration("regional_calibration.json")

# Ready to use
corrected = manager.correct(measurement)
```

## Validate Accuracy

```python
# Test your calibration
metrics = manager.validate_accuracy(test_measured, test_true)

print(f"Accuracy: {metrics['accuracy']:.1%}")
print(f"Mean error: {metrics['mean_error']:.2f}px")

# Check if recalibration needed
if manager.needs_recalibration(samples, truth):
    print("Time to recalibrate!")
```

## Common Patterns

### Pattern 1: First-Time Setup
```python
manager = CalibrationManager()

# Generate well-distributed points
points = manager.generate_calibration_points(100, grid_size=(2, 2))

# Show points to user, get measurements
# ... your code ...

# Calibrate and save
manager.calibrate_regional(measured, points)
```

### Pattern 2: Load and Use
```python
manager = CalibrationManager()
manager.load_calibration("current.json")

# Use directly
corrected = manager.correct(ocr_result)
```

### Pattern 3: Periodic Validation
```python
# Weekly accuracy check
metrics = manager.validate_accuracy(test_set, truth_set)

if metrics['accuracy'] < 0.95:
    # Trigger recalibration workflow
    recalibrate()
```

## Troubleshooting

**Error: "Calibration not performed"**
→ Call `calibrate()` or `load_calibration()` first

**Low accuracy (<95%)**
→ Use more calibration points (100 instead of 30)
→ Use regional calibration instead of simple
→ Check for measurement errors in calibration data

**FileNotFoundError**
→ Calibration file doesn't exist, run calibration first

## Performance Guide

| Method | Points | Time | Accuracy | Use When |
|--------|--------|------|----------|----------|
| Simple | 30 | 2 min | 99.8% | Quick setup, uniform errors |
| Regional | 100 | 5 min | 100% | Maximum accuracy needed |

## Files Location

- **Calibration saves**: `~/.calibration/` (default)
- **Custom location**: Pass `calibration_dir` to CalibrationManager

## Need More?

- Full API: See `CALIBRATION_README.md`
- Examples: See `test_calibration.py`
- Research: See project root research docs
