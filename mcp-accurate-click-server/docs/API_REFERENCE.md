# API Reference

Complete API documentation for all MCP tools and Python classes in the Accurate Click MCP Server.

## Table of Contents

1. [MCP Tools](#mcp-tools)
2. [Python Classes](#python-classes)
3. [Data Structures](#data-structures)
4. [Error Codes](#error-codes)
5. [Type Definitions](#type-definitions)

---

## MCP Tools

### click_on_text

Find text on screen using OCR and click it with pixel-perfect accuracy.

**MCP Tool Name**: `click_on_text`

**Description**: Captures screenshot, runs OCR to locate specified text, applies calibration correction, and executes click.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | string | Yes | - | Text to find and click on screen |
| `min_confidence` | float | No | 0.8 | Minimum OCR confidence (0.0-1.0) |
| `monitor` | integer | No | 0 | Monitor number (0=all monitors, 1+=specific) |

#### Returns

```json
{
  "success": true,
  "text_found": "Submit",
  "confidence": 0.95,
  "click_coordinates": {
    "x": 1450.5,
    "y": 950.2
  },
  "calibration_applied": true,
  "error": null
}
```

**Return Schema**:
- `success` (boolean): Whether click was executed successfully
- `text_found` (string|null): Actual text that was found
- `confidence` (float|null): OCR confidence of matched text
- `click_coordinates` (object|null): Where click was performed
  - `x` (float): X coordinate
  - `y` (float): Y coordinate
- `calibration_applied` (boolean): Whether calibration correction was used
- `error` (string|null): Error message if operation failed

#### Error Codes

| Code | Message | Cause |
|------|---------|-------|
| `TEXT_NOT_FOUND` | "Text '{text}' not found on screen" | OCR didn't detect the text |
| `OCR_FAILED` | "OCR processing failed" | OCR engine error |
| `CLICK_FAILED` | "Click execution failed" | System API error |
| `SCREENSHOT_FAILED` | "Screenshot capture failed" | Display capture error |

#### Examples

**Basic Usage:**

```python
result = server.call_tool("click_on_text", {
    "text": "Submit"
})

if result["success"]:
    print(f"Clicked '{result['text_found']}' at ({result['click_coordinates']['x']}, {result['click_coordinates']['y']})")
else:
    print(f"Error: {result['error']}")
```

**With Custom Confidence:**

```python
result = server.call_tool("click_on_text", {
    "text": "Submit",
    "min_confidence": 0.6
})
```

**On Specific Monitor:**

```python
result = server.call_tool("click_on_text", {
    "text": "File",
    "monitor": 1
})
```

---

### click_at_coordinates

Click at specific pixel coordinates with calibration correction.

**MCP Tool Name**: `click_at_coordinates`

**Description**: Executes click at specified coordinates, applying calibration if available.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `x` | float | Yes | - | X coordinate in physical pixels |
| `y` | float | Yes | - | Y coordinate in physical pixels |
| `button` | string | No | "left" | Mouse button: "left", "right", "middle" |

#### Returns

```json
{
  "success": true,
  "coordinates": {
    "requested": {"x": 1920, "y": 1080},
    "corrected": {"x": 1920.5, "y": 1079.8}
  },
  "calibration_applied": true,
  "error": null
}
```

**Return Schema**:
- `success` (boolean): Whether click was executed
- `coordinates` (object): Coordinate information
  - `requested` (object): Original coordinates
  - `corrected` (object): After calibration correction
- `calibration_applied` (boolean): Whether correction was applied
- `error` (string|null): Error message if failed

#### Error Codes

| Code | Message | Cause |
|------|---------|-------|
| `INVALID_COORDINATES` | "Coordinates out of screen bounds" | Invalid x/y values |
| `INVALID_BUTTON` | "Invalid button: {button}" | Button not in [left, right, middle] |
| `CLICK_FAILED` | "Click execution failed" | System API error |

#### Examples

```python
# Left click
result = server.call_tool("click_at_coordinates", {
    "x": 1920,
    "y": 1080
})

# Right click
result = server.call_tool("click_at_coordinates", {
    "x": 500,
    "y": 300,
    "button": "right"
})

# Middle click
result = server.call_tool("click_at_coordinates", {
    "x": 800,
    "y": 600,
    "button": "middle"
})
```

---

### get_screen_text

Extract all text elements from screen with coordinates and confidence.

**MCP Tool Name**: `get_screen_text`

**Description**: Captures screenshot, runs OCR, and returns all detected text with bounding boxes.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `monitor` | integer | No | 0 | Monitor to capture (0=all) |
| `min_confidence` | float | No | 0.7 | Minimum confidence threshold |

#### Returns

```json
{
  "success": true,
  "elements": [
    {
      "text": "Submit",
      "confidence": 0.95,
      "x": 1450.5,
      "y": 950.2,
      "bbox": {
        "x_min": 1400,
        "y_min": 930,
        "x_max": 1500,
        "y_max": 970
      },
      "width": 100,
      "height": 40
    },
    {
      "text": "Cancel",
      "confidence": 0.93,
      "x": 1350.5,
      "y": 950.2,
      "bbox": {
        "x_min": 1300,
        "y_min": 930,
        "x_max": 1400,
        "y_max": 970
      },
      "width": 100,
      "height": 40
    }
  ],
  "total_elements": 2,
  "screenshot_size": {
    "width": 1920,
    "height": 1080
  },
  "error": null
}
```

**Return Schema**:
- `success` (boolean): Whether operation succeeded
- `elements` (array): List of detected text elements
  - `text` (string): Detected text content
  - `confidence` (float): OCR confidence (0.0-1.0)
  - `x`, `y` (float): Center coordinates
  - `bbox` (object): Bounding box
    - `x_min`, `y_min`, `x_max`, `y_max` (float): Box corners
  - `width`, `height` (float): Element dimensions
- `total_elements` (integer): Count of elements found
- `screenshot_size` (object): Screenshot dimensions
- `error` (string|null): Error message if failed

#### Error Codes

| Code | Message | Cause |
|------|---------|-------|
| `OCR_FAILED` | "OCR processing failed" | OCR engine error |
| `SCREENSHOT_FAILED` | "Screenshot capture failed" | Display capture error |

#### Examples

```python
# Get all text
result = server.call_tool("get_screen_text", {})

for elem in result["elements"]:
    print(f"'{elem['text']}' at ({elem['x']}, {elem['y']})")
    print(f"  Confidence: {elem['confidence']:.1%}")

# With custom confidence
result = server.call_tool("get_screen_text", {
    "min_confidence": 0.9
})

# Specific monitor
result = server.call_tool("get_screen_text", {
    "monitor": 1
})
```

---

### calibrate_system

Run interactive calibration to improve click accuracy.

**MCP Tool Name**: `calibrate_system`

**Description**: Displays calibration points on screen, records user clicks, computes correction matrix.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `num_points` | integer | No | 20 | Number of calibration points |
| `save_file` | string | No | null | File path to save calibration |

#### Returns

```json
{
  "success": true,
  "calibration": {
    "num_points": 20,
    "mean_error": 0.707,
    "median_error": 0.667,
    "max_error": 2.152,
    "std_error": 0.370,
    "inlier_ratio": 1.0
  },
  "saved_to": "calibration.npz",
  "error": null
}
```

**Return Schema**:
- `success` (boolean): Whether calibration completed
- `calibration` (object): Calibration metrics
  - `num_points` (integer): Points used for calibration
  - `mean_error` (float): Mean error in pixels
  - `median_error` (float): Median error in pixels
  - `max_error` (float): Maximum error in pixels
  - `std_error` (float): Standard deviation
  - `inlier_ratio` (float): RANSAC inlier ratio (0.0-1.0)
- `saved_to` (string|null): File path if saved
- `error` (string|null): Error message if failed

#### Error Codes

| Code | Message | Cause |
|------|---------|-------|
| `INSUFFICIENT_POINTS` | "Need at least 4 points, got {n}" | Too few points |
| `CALIBRATION_FAILED` | "Failed to compute calibration" | Math/computation error |
| `SAVE_FAILED` | "Failed to save calibration file" | File I/O error |

#### Examples

```python
# Quick calibration
result = server.call_tool("calibrate_system", {
    "num_points": 20
})

print(f"Mean error: {result['calibration']['mean_error']:.2f}px")

# High-accuracy calibration with save
result = server.call_tool("calibrate_system", {
    "num_points": 50,
    "save_file": "high_accuracy.npz"
})

print(f"Saved to: {result['saved_to']}")
```

---

### get_calibration_status

Get current calibration status and accuracy metrics.

**MCP Tool Name**: `get_calibration_status`

**Description**: Returns whether system is calibrated and calibration quality metrics.

#### Parameters

None.

#### Returns

```json
{
  "is_calibrated": true,
  "calibration": {
    "num_points": 20,
    "mean_error": 0.707,
    "median_error": 0.667,
    "max_error": 2.152,
    "std_error": 0.370
  },
  "file_loaded": "calibration.npz"
}
```

**Return Schema**:
- `is_calibrated` (boolean): Whether calibration is active
- `calibration` (object|null): Calibration metrics if calibrated
  - `num_points` (integer): Number of calibration points
  - `mean_error` (float): Mean calibration error (pixels)
  - `median_error` (float): Median error (pixels)
  - `max_error` (float): Maximum error (pixels)
  - `std_error` (float): Standard deviation (pixels)
- `file_loaded` (string|null): Loaded calibration file path

#### Examples

```python
result = server.call_tool("get_calibration_status", {})

if result["is_calibrated"]:
    print(f"✓ Calibrated with {result['calibration']['num_points']} points")
    print(f"  Accuracy: {result['calibration']['mean_error']:.2f}px mean error")
else:
    print("✗ Not calibrated - run calibrate_system for better accuracy")
```

---

### get_system_info

Get display configuration and system information.

**MCP Tool Name**: `get_system_info`

**Description**: Returns monitor configurations, DPI settings, and virtual desktop information.

#### Parameters

None.

#### Returns

```json
{
  "monitors": [
    {
      "index": 0,
      "bounds": {
        "left": 0,
        "top": 0,
        "right": 1920,
        "bottom": 1080
      },
      "resolution": {
        "width": 1920,
        "height": 1080
      },
      "dpi": {
        "x": 96,
        "y": 96
      },
      "scale": 1.0,
      "primary": true
    },
    {
      "index": 1,
      "bounds": {
        "left": 1920,
        "top": 0,
        "right": 3840,
        "bottom": 1080
      },
      "resolution": {
        "width": 1920,
        "height": 1080
      },
      "dpi": {
        "x": 144,
        "y": 144
      },
      "scale": 1.5,
      "primary": false
    }
  ],
  "virtual_screen": {
    "left": 0,
    "top": 0,
    "width": 3840,
    "height": 1080
  },
  "calibrated": true,
  "platform": "Windows 10",
  "dpi_awareness": "PerMonitorV2"
}
```

**Return Schema**:
- `monitors` (array): List of connected monitors
  - `index` (integer): Monitor number
  - `bounds` (object): Position and size
  - `resolution` (object): Width and height
  - `dpi` (object): DPI x and y
  - `scale` (float): DPI scale factor
  - `primary` (boolean): Is primary monitor
- `virtual_screen` (object): Virtual desktop bounds
- `calibrated` (boolean): Calibration status
- `platform` (string): Operating system
- `dpi_awareness` (string): DPI awareness mode

#### Examples

```python
result = server.call_tool("get_system_info", {})

print(f"Platform: {result['platform']}")
print(f"Monitors: {len(result['monitors'])}")

for monitor in result["monitors"]:
    print(f"\nMonitor {monitor['index']}:")
    print(f"  Resolution: {monitor['resolution']['width']}×{monitor['resolution']['height']}")
    print(f"  DPI: {monitor['dpi']['x']} ({monitor['scale']*100:.0f}% scaling)")
    print(f"  Primary: {monitor['primary']}")
```

---

### take_screenshot

Capture screenshot of specified monitor.

**MCP Tool Name**: `take_screenshot`

**Description**: Captures screenshot and optionally saves to file.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `monitor` | integer | No | 0 | Monitor to capture (0=all) |
| `save_path` | string | No | null | File path to save image |

#### Returns

```json
{
  "success": true,
  "screenshot": {
    "width": 1920,
    "height": 1080,
    "format": "RGB",
    "path": "screenshot.png"
  },
  "error": null
}
```

**Return Schema**:
- `success` (boolean): Whether capture succeeded
- `screenshot` (object): Screenshot information
  - `width`, `height` (integer): Dimensions
  - `format` (string): Image format
  - `path` (string|null): Saved file path
- `error` (string|null): Error message if failed

#### Error Codes

| Code | Message | Cause |
|------|---------|-------|
| `SCREENSHOT_FAILED` | "Screenshot capture failed" | Display capture error |
| `SAVE_FAILED` | "Failed to save screenshot" | File I/O error |

#### Examples

```python
# Capture without saving
result = server.call_tool("take_screenshot", {})
print(f"Captured {result['screenshot']['width']}×{result['screenshot']['height']}")

# Capture and save
result = server.call_tool("take_screenshot", {
    "save_path": "screen.png"
})
print(f"Saved to: {result['screenshot']['path']}")

# Specific monitor
result = server.call_tool("take_screenshot", {
    "monitor": 1,
    "save_path": "monitor1.png"
})
```

---

## Python Classes

### AccurateClickSystem

Main class integrating all components for accurate clicking.

```python
class AccurateClickSystem:
    """Complete accurate click system"""

    def __init__(self,
                 use_calibration: bool = True,
                 use_gpu: bool = False,
                 ocr_lang: str = 'en',
                 calibration_file: Optional[str] = None)
```

#### Methods

##### `click_on_text(text, min_confidence=0.8, monitor=0) -> bool`

Find and click on text.

**Parameters:**
- `text` (str): Text to find
- `min_confidence` (float): Minimum OCR confidence
- `monitor` (int): Monitor number

**Returns:** `bool` - Success status

##### `click_at_coordinates(x, y, button='left') -> bool`

Click at specific coordinates.

**Parameters:**
- `x`, `y` (float): Coordinates in pixels
- `button` (str): Mouse button

**Returns:** `bool` - Success status

##### `get_screen_text(monitor=0, min_confidence=0.7) -> List[Dict]`

Extract all text from screen.

**Parameters:**
- `monitor` (int): Monitor number
- `min_confidence` (float): Minimum confidence

**Returns:** `List[Dict]` - Text elements

##### `calibrate_system(num_points=20, save_file=None)`

Run calibration workflow.

**Parameters:**
- `num_points` (int): Number of calibration points
- `save_file` (str, optional): File to save calibration

##### `get_calibration_status() -> Dict`

Get calibration status.

**Returns:** `Dict` with calibration metrics

##### `get_system_info() -> Dict`

Get system information.

**Returns:** `Dict` with monitor and system info

---

### DPIManager

Manages DPI awareness and coordinate conversions.

```python
class DPIManager:
    """DPI management for Windows/Linux"""

    def __init__(self)
```

#### Methods

##### `get_monitor_at_point(x, y) -> MonitorInfo`

Get monitor containing point.

##### `get_all_monitors() -> List[MonitorInfo]`

Get all connected monitors.

##### `get_virtual_screen_bounds() -> Dict`

Get virtual desktop bounds.

##### `physical_to_logical(x, y) -> Tuple[float, float]`

Convert physical to logical pixels.

##### `logical_to_physical(x, y) -> Tuple[int, int]`

Convert logical to physical pixels.

---

### OCREngine

OCR wrapper for text detection.

```python
class OCREngine:
    """PaddleOCR wrapper"""

    def __init__(self, lang='en', use_gpu=False)
```

#### Methods

##### `extract_text(image_path) -> List[BoundingBox]`

Extract all text from image.

**Returns:** List of `BoundingBox` objects

##### `find_text(image_path, target_text, min_confidence=0.8) -> Optional[BoundingBox]`

Find specific text.

**Returns:** `BoundingBox` or `None`

---

### CalibrationSystem

Homography-based calibration.

```python
class CalibrationSystem:
    """Calibration with RANSAC"""

    def __init__(self)
```

#### Methods

##### `add_calibration_point(ocr_point, actual_point)`

Add calibration correspondence.

##### `compute_calibration(use_ransac=True)`

Compute homography from points.

##### `apply_correction(point) -> Tuple[float, float]`

Apply calibration to point.

##### `get_calibration_errors() -> np.ndarray`

Get calibration errors for all points.

##### `save_calibration(filepath)`

Save calibration to file.

##### `load_calibration(filepath)`

Load calibration from file.

---

### ClickExecutor

Click execution with SendInput/XTest.

```python
class ClickExecutor:
    """Cross-platform click execution"""

    def __init__(self, dpi_manager: DPIManager)
```

#### Methods

##### `click(x, y, button='left') -> bool`

Execute click at coordinates.

**Parameters:**
- `x`, `y` (float): Physical pixel coordinates
- `button` (str): Mouse button

**Returns:** `bool` - Success status

---

## Data Structures

### BoundingBox

```python
@dataclass
class BoundingBox:
    """OCR bounding box"""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    text: str
    confidence: float

    @property
    def center(self) -> Tuple[float, float]:
        """Get center point"""

    @property
    def width(self) -> float:
        """Get width"""

    @property
    def height(self) -> float:
        """Get height"""
```

### MonitorInfo

```python
@dataclass
class MonitorInfo:
    """Monitor information"""
    handle: int
    left: int
    top: int
    right: int
    bottom: int
    dpi_x: int
    dpi_y: int
    is_primary: bool

    @property
    def width(self) -> int:
        """Monitor width"""

    @property
    def height(self) -> int:
        """Monitor height"""

    @property
    def scale_factor(self) -> float:
        """DPI scale factor"""
```

---

## Error Codes

### General Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_PARAMETERS` | 400 | Invalid or missing parameters |
| `INTERNAL_ERROR` | 500 | Internal server error |

### OCR Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `OCR_FAILED` | 500 | OCR engine error |
| `TEXT_NOT_FOUND` | 404 | Text not detected on screen |

### Click Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `CLICK_FAILED` | 500 | Click execution failed |
| `INVALID_COORDINATES` | 400 | Coordinates out of bounds |
| `INVALID_BUTTON` | 400 | Invalid button name |

### Calibration Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `CALIBRATION_FAILED` | 500 | Calibration computation failed |
| `INSUFFICIENT_POINTS` | 400 | Not enough calibration points |
| `FILE_NOT_FOUND` | 404 | Calibration file not found |
| `SAVE_FAILED` | 500 | Failed to save calibration |

### System Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `SCREENSHOT_FAILED` | 500 | Screenshot capture failed |
| `MONITOR_NOT_FOUND` | 404 | Invalid monitor index |

---

## Type Definitions

### TypeScript/JSON Schema

```typescript
// Text element
interface TextElement {
  text: string;
  confidence: number;
  x: number;
  y: number;
  bbox: {
    x_min: number;
    y_min: number;
    x_max: number;
    y_max: number;
  };
  width: number;
  height: number;
}

// Monitor info
interface Monitor {
  index: number;
  bounds: {
    left: number;
    top: number;
    right: number;
    bottom: number;
  };
  resolution: {
    width: number;
    height: number;
  };
  dpi: {
    x: number;
    y: number;
  };
  scale: number;
  primary: boolean;
}

// Calibration metrics
interface CalibrationMetrics {
  num_points: number;
  mean_error: number;
  median_error: number;
  max_error: number;
  std_error: number;
  inlier_ratio?: number;
}
```

---

**For usage examples, see [USAGE_GUIDE.md](USAGE_GUIDE.md)**
**For system architecture, see [ARCHITECTURE.md](ARCHITECTURE.md)**
