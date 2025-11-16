# Test Fixtures

This directory contains test data and fixtures for the MCP Accurate Click Server test suite.

## Files

### `sample_calibration_data.json`
Pre-generated calibration data for testing calibration algorithms.

**Contents:**
- 30 calibration points in a grid pattern
- True coordinates (ground truth)
- Measured coordinates (with simulated OCR error)
- Expected offset: [3.5, -2.8]
- Expected accuracy metrics

**Usage:**
```python
import json
from pathlib import Path

fixtures_dir = Path(__file__).parent / "fixtures"
with open(fixtures_dir / "sample_calibration_data.json") as f:
    calib_data = json.load(f)

true_points = np.array(calib_data["true_points"])
measured_points = np.array(calib_data["measured_points"])
```

### `mock_ocr_results.json`
Mock OCR detection results for testing OCR processing and text extraction.

**Contents:**
- 10 sample text detections
- Bounding boxes in PaddleOCR format
- Confidence scores
- Extracted text
- Center point coordinates

**Usage:**
```python
with open(fixtures_dir / "mock_ocr_results.json") as f:
    ocr_data = json.load(f)

for detection in ocr_data["detections"]:
    bbox = detection["bbox"]
    text = detection["text"]
    confidence = detection["confidence"]
```

### `window_configurations.json`
Sample window configurations for testing real-world clicking scenarios.

**Contents:**
- 5 different window types (dialog, main, notification, panel, maximized)
- Window positions and sizes
- UI elements within each window
- Test scenarios for each window

**Usage:**
```python
with open(fixtures_dir / "window_configurations.json") as f:
    window_data = json.load(f)

for window in window_data["windows"]:
    x, y = window["x"], window["y"]
    width, height = window["width"], window["height"]

    for element in window["ui_elements"]:
        # Calculate absolute position
        abs_x = x + element["local_x"]
        abs_y = y + element["local_y"]
```

## Adding New Fixtures

When adding new test fixtures:

1. **Use JSON format** for structured data
2. **Include description** at the top of the file
3. **Document schema** in this README
4. **Add usage examples** showing how to load and use the data
5. **Keep data realistic** - simulate real-world scenarios
6. **Version control** - commit fixtures to git

## Fixture Generation

Some fixtures can be regenerated using the fixture generator script:

```bash
python tests/generate_fixtures.py
```

This will regenerate all fixtures with fresh random seeds while maintaining the same structure.

## Fixture Types

### Calibration Data
- Grid patterns for systematic testing
- Random distributions for statistical validation
- Regional patterns for testing regional calibration

### OCR Results
- Various text lengths and positions
- Different confidence levels
- Edge cases (corners, edges, overlapping text)

### Window Configurations
- Different window sizes (small, medium, large, maximized)
- Different positions (centered, edge, corner)
- Different UI element types (buttons, menus, links, checkboxes)

## Testing with Fixtures

Fixtures are automatically available in tests via pytest fixtures:

```python
def test_with_fixture(fixtures_dir):
    """Test using fixture directory"""
    data_file = fixtures_dir / "sample_calibration_data.json"
    with open(data_file) as f:
        data = json.load(f)

    # Use data in test...
```

Or load directly in test setup:

```python
@pytest.fixture
def calibration_data():
    """Load calibration data fixture"""
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "sample_calibration_data.json") as f:
        return json.load(f)

def test_calibration(calibration_data):
    """Test using loaded calibration data"""
    true_points = np.array(calibration_data["true_points"])
    # Test...
```

## Maintenance

Fixtures should be:
- **Reviewed** when test requirements change
- **Updated** when adding new test scenarios
- **Validated** to ensure they represent realistic data
- **Documented** with clear descriptions and examples
