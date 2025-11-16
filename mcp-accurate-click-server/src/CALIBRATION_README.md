# Calibration System Documentation

## Overview

This calibration system implements the research findings that achieved **99.8-100% click accuracy** using systematic offset correction. The system provides three levels of calibration:

1. **SimpleCalibration**: Offset-based calibration (99.8% accuracy with 30 points)
2. **RegionalCalibration**: 2x2 grid calibration (100% accuracy with 100 points)
3. **CalibrationManager**: High-level manager for complete workflows

## Research Background

Our research demonstrated that:
- **Simple offset calibration** with 30 points achieves 99.8% accuracy (within 2px)
- **Regional 2x2 grid calibration** with 100 points achieves 100% accuracy
- Mean offset computation is the most effective correction method
- Systematic errors can be reliably calibrated out using these techniques

## Installation

```python
# No external dependencies beyond NumPy and SciPy
pip install numpy scipy
```

## Quick Start

### Simple Calibration (99.8% accuracy)

```python
from calibration import SimpleCalibration
import numpy as np

# Step 1: Collect calibration data
# measured_points: coordinates from OCR/vision system
# true_points: actual click locations
measured_points = np.array([[105.3, 97.2], [503.8, 497.1], ...])
true_points = np.array([[100, 100], [500, 500], ...])

# Step 2: Calibrate
cal = SimpleCalibration()
metadata = cal.calibrate(measured_points, true_points)

print(f"Accuracy: {metadata.accuracy:.1%}")
print(f"Mean error: {metadata.mean_error:.2f}px")

# Step 3: Correct new measurements
new_measurement = np.array([755.4, 432.1])
corrected = cal.correct(new_measurement)

# Step 4: Save for later use
cal.save("calibration.json")
```

### Regional Calibration (100% accuracy)

```python
from calibration import RegionalCalibration

# Collect 100 calibration points distributed across screen
# (use CalibrationManager.generate_calibration_points for this)
measured_points = np.array([...])  # 100 measured coordinates
true_points = np.array([...])      # 100 true coordinates

# Calibrate with 2x2 regional grid
cal = RegionalCalibration(grid_size=(2, 2))
metadata = cal.calibrate(measured_points, true_points)

# Corrections are now region-aware
corrected = cal.correct(new_measurement)

# Save regional calibration
cal.save("regional_calibration.json")
```

### Complete Workflow with CalibrationManager

```python
from calibration import CalibrationManager

# Initialize manager
manager = CalibrationManager()

# Generate calibration points (evenly distributed across regions)
calibration_points = manager.generate_calibration_points(
    n_points=100,
    grid_size=(2, 2)
)

# Display these points to user, collect measurements
# ... user interaction code ...

# Calibrate
metadata = manager.calibrate_regional(
    measured_points,
    calibration_points,
    grid_size=(2, 2)
)

# Use calibration
corrected = manager.correct(new_measurement)

# Validate accuracy periodically
test_measured = np.array([...])
test_true = np.array([...])

metrics = manager.validate_accuracy(test_measured, test_true)
print(f"Current accuracy: {metrics['accuracy']:.1%}")

# Check if recalibration needed
if manager.needs_recalibration(test_measured, test_true):
    print("Recalibration recommended!")
```

## API Reference

### SimpleCalibration

**Purpose**: Basic offset-based calibration achieving 99.8% accuracy.

#### Methods

```python
calibrate(measured_points: np.ndarray, true_points: np.ndarray) -> CalibrationMetadata
```
Calibrate using measured and true coordinate pairs.
- **measured_points**: Array of shape (N, 2) with measured coordinates
- **true_points**: Array of shape (N, 2) with true coordinates
- **Returns**: Metadata with accuracy statistics

```python
correct(measured_coord: np.ndarray) -> np.ndarray
```
Apply calibration correction to a coordinate.
- **measured_coord**: Single coordinate (x, y)
- **Returns**: Corrected coordinate (x, y)

```python
save(filepath: str) -> None
```
Save calibration to JSON file.

```python
load(filepath: str) -> CalibrationMetadata
```
Load calibration from JSON file.

### RegionalCalibration

**Purpose**: Advanced regional calibration achieving 100% accuracy.

#### Constructor

```python
RegionalCalibration(
    grid_size: Tuple[int, int] = (2, 2),
    screen_width: int = 1920,
    screen_height: int = 1080
)
```

#### Methods

```python
calibrate(measured_points: np.ndarray, true_points: np.ndarray) -> CalibrationMetadata
```
Calibrate with regional offset computation.
- Automatically assigns points to regions
- Computes separate offset for each region
- Uses global offset as fallback for sparse regions

```python
correct(measured_coord: np.ndarray) -> np.ndarray
```
Apply region-specific correction.
- Automatically detects which region the coordinate is in
- Applies appropriate regional offset

```python
get_region_info() -> Dict[str, Any]
```
Get detailed information about regional calibration.

### CalibrationManager

**Purpose**: High-level manager for complete calibration workflows.

#### Constructor

```python
CalibrationManager(
    screen_width: int = 1920,
    screen_height: int = 1080,
    calibration_dir: Optional[str] = None  # defaults to ~/.calibration
)
```

#### Key Methods

```python
generate_calibration_points(
    n_points: int,
    grid_size: Optional[Tuple[int, int]] = None,
    margin: int = 100,
    seed: Optional[int] = None
) -> np.ndarray
```
Generate evenly distributed calibration points.
- **grid_size**: If specified, ensures points in all regions
- **margin**: Distance from screen edges
- **Returns**: Array of points (N, 2)

```python
calibrate_simple(
    measured_points: np.ndarray,
    true_points: np.ndarray,
    save_name: str = "simple_calibration.json"
) -> CalibrationMetadata
```
Perform simple calibration and save.

```python
calibrate_regional(
    measured_points: np.ndarray,
    true_points: np.ndarray,
    grid_size: Tuple[int, int] = (2, 2),
    save_name: str = "regional_calibration.json"
) -> CalibrationMetadata
```
Perform regional calibration and save.

```python
load_calibration(filename: str) -> CalibrationMetadata
```
Load previously saved calibration.

```python
validate_accuracy(
    measured_points: np.ndarray,
    true_points: np.ndarray,
    threshold: float = 2.0
) -> Dict[str, float]
```
Validate calibration on test set.
- Returns metrics including mean_error, accuracy, within_1px, etc.

```python
needs_recalibration(
    measured_points: np.ndarray,
    true_points: np.ndarray,
    accuracy_threshold: float = 0.95
) -> bool
```
Detect if recalibration is needed.

## Calibration File Format

Calibration data is saved in JSON format:

### Simple Calibration

```json
{
  "calibration_type": "simple",
  "offset": [3.5, -2.8],
  "metadata": {
    "timestamp": "2025-11-16T19:35:03.849863",
    "num_points": 30,
    "accuracy": 0.998,
    "mean_error": 0.598,
    "std_error": 0.331,
    "calibration_type": "simple",
    "screen_width": 1920,
    "screen_height": 1080
  },
  "screen_width": 1920,
  "screen_height": 1080
}
```

### Regional Calibration

```json
{
  "calibration_type": "regional",
  "grid_size": [2, 2],
  "regional_offsets": {
    "0,0": [3.49, -2.70],
    "0,1": [3.50, -2.67],
    "1,0": [3.61, -2.95],
    "1,1": [3.56, -2.77]
  },
  "global_offset": [3.54, -2.77],
  "metadata": {
    "timestamp": "2025-11-16T19:35:03.849863",
    "num_points": 100,
    "accuracy": 1.0,
    "mean_error": 0.251,
    "std_error": 0.185,
    "calibration_type": "regional_2x2",
    "screen_width": 1920,
    "screen_height": 1080
  },
  "screen_width": 1920,
  "screen_height": 1080
}
```

## Best Practices

### Calibration Point Selection

1. **Simple Calibration** (99.8% accuracy):
   - Use 30+ points
   - Distribute evenly across screen
   - Include corners and edges
   - Avoid clustering

2. **Regional Calibration** (100% accuracy):
   - Use 100+ points
   - Ensure points in all regions (use `generate_calibration_points` with `grid_size`)
   - 2x2 grid is optimal for 1920x1080 screens
   - Consider 3x3 for larger or ultra-wide screens

### When to Use Each Method

- **SimpleCalibration**:
  - Quick setup needed
  - 99.8% accuracy sufficient
  - Uniform systematic errors
  - Limited calibration time

- **RegionalCalibration**:
  - Maximum accuracy required (100%)
  - Non-uniform systematic errors
  - Different DPI settings across screen
  - Critical applications

### Validation and Maintenance

```python
# Validate regularly (e.g., weekly)
metrics = manager.validate_accuracy(test_measured, test_true)

if metrics['accuracy'] < 0.95:
    print("Recalibration needed!")
    # Run calibration workflow again

# Check calibration age
summary = manager.get_calibration_summary()
timestamp = summary['metadata']['timestamp']
# Recalibrate if older than 30 days
```

### Error Handling

```python
try:
    corrected = manager.correct(measured_coord)
except RuntimeError:
    # No calibration loaded
    print("Please calibrate first")
    # Run calibration workflow
```

## Performance Metrics

Based on our research with 500+ test points:

### Simple Calibration (30 points)
- **Mean error**: ~0.7px
- **Accuracy (≤2px)**: 99.8%
- **Within 1px**: ~85%
- **Setup time**: ~2 minutes

### Regional Calibration (100 points)
- **Mean error**: ~0.25px
- **Accuracy (≤2px)**: 100%
- **Within 1px**: ~98%
- **Setup time**: ~5 minutes

## Integration Example

### Complete MCP Server Integration

```python
from calibration import CalibrationManager
import numpy as np

class AccurateClickServer:
    def __init__(self):
        self.calibration_manager = CalibrationManager()

        # Try to load existing calibration
        try:
            self.calibration_manager.load_calibration("current.json")
            print("Calibration loaded successfully")
        except FileNotFoundError:
            print("No calibration found - please calibrate")

    def calibrate(self, n_points=100):
        """Interactive calibration workflow"""
        # Generate calibration points
        points = self.calibration_manager.generate_calibration_points(
            n_points=n_points,
            grid_size=(2, 2)
        )

        # Display points to user and collect measurements
        measured_points = []
        for true_point in points:
            # Show marker at true_point
            # Measure where OCR detects it
            measured = self.measure_marker(true_point)
            measured_points.append(measured)

        measured_points = np.array(measured_points)

        # Calibrate
        metadata = self.calibration_manager.calibrate_regional(
            measured_points,
            points,
            grid_size=(2, 2),
            save_name="current.json"
        )

        return metadata

    def click(self, target_text: str):
        """Click on text with calibration correction"""
        # Use OCR to find text
        measured_coord = self.ocr_find_text(target_text)

        # Apply calibration correction
        corrected_coord = self.calibration_manager.correct(measured_coord)

        # Perform click
        self.perform_click(corrected_coord)

        return corrected_coord
```

## Testing

Run the comprehensive test suite:

```bash
python test_calibration.py
```

This tests:
- Simple and regional calibration
- Save/load functionality
- Edge cases and error handling
- Validation and accuracy metrics

## Support

For issues or questions:
1. Check the test suite for usage examples
2. Review the research documents (COMPREHENSIVE_RESEARCH_REPORT.md)
3. Examine test_simple_accuracy.py and test_ultra_accuracy.py

## License

Part of the Pixel Coordinates for Computer Use project.
