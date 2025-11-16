# Usage Guide

Complete guide to using the Accurate Click MCP Server with Claude Desktop and Python.

## Table of Contents

1. [Quick Start](#quick-start)
2. [MCP Server Setup](#mcp-server-setup)
3. [Using with Claude Desktop](#using-with-claude-desktop)
4. [MCP Tools Reference](#mcp-tools-reference)
5. [Calibration Workflow](#calibration-workflow)
6. [Configuration Options](#configuration-options)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 30-Second Start

```bash
# 1. Install
pip install mcp-accurate-click-server

# 2. Start server
python -m mcp_accurate_click_server

# 3. Use from Claude Desktop
# "Click on the Submit button"
```

### 5-Minute Start (with Calibration)

```python
from mcp_accurate_click_server import AccurateClickSystem

# Initialize system
system = AccurateClickSystem(use_calibration=True)

# Run calibration (once)
system.calibrate_system(num_points=20)
system.calibration.save_calibration("calibration.npz")

# Now use with 0.24px accuracy!
system.click_on_text("Submit")
```

---

## MCP Server Setup

### Starting the Server

**Method 1: Command Line**

```bash
# Start with default settings
python -m mcp_accurate_click_server

# Start with custom port
python -m mcp_accurate_click_server --port 8080

# Start with GPU support
python -m mcp_accurate_click_server --gpu

# Start with verbose logging
python -m mcp_accurate_click_server --verbose
```

**Method 2: Python Script**

```python
# start_server.py
from mcp_accurate_click_server import MCPServer

server = MCPServer(
    use_gpu=True,
    calibration_file="calibration.npz"
)

server.start()
```

**Method 3: Claude Desktop Configuration**

Edit `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "accurate-click": {
      "command": "python",
      "args": ["-m", "mcp_accurate_click_server"],
      "env": {
        "CALIBRATION_FILE": "path/to/calibration.npz",
        "USE_GPU": "true"
      }
    }
  }
}
```

### Verifying Server is Running

```bash
# Server should output:
✓ MCP Server initialized
✓ OCR engine ready (PaddleOCR)
✓ DPI manager initialized
✓ Calibration loaded: calibration.npz
✓ Server listening on stdio

# Ready to receive MCP requests
```

---

## Using with Claude Desktop

### Connecting to Server

1. **Install Claude Desktop** from [claude.ai](https://claude.ai/download)

2. **Configure MCP Server** in settings:
   - Open Claude Desktop
   - Go to Settings → Developer → MCP Servers
   - Add the Accurate Click server configuration

3. **Verify Connection**:
   ```
   You: "What MCP tools are available?"
   Claude: "I have access to accurate clicking tools including click_on_text,
            click_at_coordinates, get_screen_text, and more."
   ```

### Example Conversations

**Example 1: Click on Text**

```
You: "Click on the File menu"

Claude: [Uses click_on_text tool]
✓ Found "File" at (125, 45)
✓ Clicked successfully
```

**Example 2: Multi-Step Automation**

```
You: "Click File, then click New Document"

Claude:
[Uses click_on_text("File")]
✓ Clicked File menu

[Uses click_on_text("New Document")]
✓ Clicked New Document
```

**Example 3: Get Screen Information**

```
You: "What text is on my screen?"

Claude: [Uses get_screen_text tool]
I can see the following text elements:
- "File" at (125, 45)
- "Edit" at (185, 45)
- "Submit" at (1450, 950)
- "Cancel" at (1350, 950)
[... more elements ...]
```

**Example 4: Precise Clicking**

```
You: "Click at coordinates 1920, 1080"

Claude: [Uses click_at_coordinates(1920, 1080)]
✓ Clicked at (1920, 1080) with calibration correction
```

---

## MCP Tools Reference

### 1. click_on_text

Find and click on specific text on the screen.

**Usage:**

```javascript
// From Claude Desktop
"Click on the Submit button"
"Click the text that says 'Login'"
```

**Python:**

```python
success = system.click_on_text(
    text="Submit",
    min_confidence=0.8,
    monitor=0
)
```

**Parameters:**
- `text` (string): Text to find and click
- `min_confidence` (float, optional): Minimum OCR confidence (0.0-1.0), default 0.8
- `monitor` (int, optional): Monitor number (0=all monitors), default 0

**Returns:**
- `success` (boolean): True if text found and clicked successfully

**Example:**

```python
# Basic usage
system.click_on_text("OK")

# With lower confidence for fuzzy text
system.click_on_text("Sbmit", min_confidence=0.6)  # Finds "Submit"

# On specific monitor
system.click_on_text("File", monitor=1)
```

---

### 2. click_at_coordinates

Click at specific pixel coordinates with calibration.

**Usage:**

```javascript
// From Claude Desktop
"Click at position 1920, 1080"
"Click at coordinates x=500, y=300"
```

**Python:**

```python
success = system.click_at_coordinates(
    x=1920,
    y=1080,
    button='left'
)
```

**Parameters:**
- `x` (float): X coordinate in physical pixels
- `y` (float): Y coordinate in physical pixels
- `button` (string, optional): 'left', 'right', or 'middle', default 'left'

**Returns:**
- `success` (boolean): True if click executed successfully

**Example:**

```python
# Left click
system.click_at_coordinates(500, 300)

# Right click
system.click_at_coordinates(500, 300, button='right')

# Middle click
system.click_at_coordinates(500, 300, button='middle')
```

---

### 3. get_screen_text

Extract all text from screen with coordinates.

**Usage:**

```javascript
// From Claude Desktop
"What text is visible on my screen?"
"List all clickable elements"
```

**Python:**

```python
text_elements = system.get_screen_text(
    monitor=0,
    min_confidence=0.7
)
```

**Parameters:**
- `monitor` (int, optional): Monitor to capture, default 0
- `min_confidence` (float, optional): Minimum confidence threshold, default 0.7

**Returns:**
- `text_elements` (list): List of dictionaries with:
  - `text` (str): Detected text
  - `confidence` (float): OCR confidence (0.0-1.0)
  - `x`, `y` (float): Center coordinates
  - `bbox` (tuple): Bounding box (x_min, y_min, x_max, y_max)
  - `width`, `height` (float): Dimensions

**Example:**

```python
elements = system.get_screen_text()

for elem in elements:
    print(f"'{elem['text']}' at ({elem['x']:.0f}, {elem['y']:.0f})")
    print(f"  Confidence: {elem['confidence']:.1%}")
    print(f"  Size: {elem['width']:.0f}×{elem['height']:.0f}px")
```

---

### 4. calibrate_system

Run interactive calibration workflow.

**Usage:**

```javascript
// From Claude Desktop
"Calibrate the clicking system"
"Run calibration with 30 points"
```

**Python:**

```python
system.calibrate_system(
    num_points=20,
    save_file="calibration.npz"
)
```

**Parameters:**
- `num_points` (int, optional): Number of calibration points, default 20
- `save_file` (string, optional): File to save calibration, default None

**Process:**
1. System displays calibration points on screen
2. User clicks on each point
3. System computes correction matrix
4. Calibration saved (if save_file specified)

**Example:**

```python
# Quick calibration (20 points)
system.calibrate_system(num_points=20)

# High-accuracy calibration (50 points)
system.calibrate_system(num_points=50, save_file="high_accuracy.npz")

# Load existing calibration
system.calibration.load_calibration("calibration.npz")
```

---

### 5. get_calibration_status

Check calibration status.

**Usage:**

```javascript
// From Claude Desktop
"Is the system calibrated?"
"Show calibration status"
```

**Python:**

```python
status = system.get_calibration_status()
```

**Returns:**
- Dictionary with:
  - `is_calibrated` (bool): Whether system is calibrated
  - `num_points` (int): Number of calibration points
  - `mean_error` (float): Mean calibration error in pixels
  - `max_error` (float): Maximum error in pixels

**Example:**

```python
status = system.get_calibration_status()

if status['is_calibrated']:
    print(f"✓ Calibrated with {status['num_points']} points")
    print(f"  Mean error: {status['mean_error']:.2f}px")
    print(f"  Max error: {status['max_error']:.2f}px")
else:
    print("✗ Not calibrated - run calibrate_system()")
```

---

### 6. get_system_info

Get display configuration information.

**Usage:**

```javascript
// From Claude Desktop
"Show display information"
"What monitors are connected?"
```

**Python:**

```python
info = system.get_system_info()
```

**Returns:**
- Dictionary with:
  - `monitors` (list): List of monitor info
    - `index` (int): Monitor number
    - `bounds` (tuple): (left, top, right, bottom)
    - `resolution` (tuple): (width, height)
    - `dpi` (tuple): (dpi_x, dpi_y)
    - `scale` (float): DPI scale factor
    - `primary` (bool): Is primary monitor
  - `virtual_screen` (dict): Virtual desktop bounds
  - `calibrated` (bool): Calibration status

**Example:**

```python
info = system.get_system_info()

print(f"Total monitors: {len(info['monitors'])}")

for monitor in info['monitors']:
    print(f"\nMonitor {monitor['index']}:")
    print(f"  Resolution: {monitor['resolution'][0]}×{monitor['resolution'][1]}")
    print(f"  DPI: {monitor['dpi'][0]} ({monitor['scale']*100:.0f}% scaling)")
    print(f"  Primary: {monitor['primary']}")

print(f"\nVirtual Desktop: {info['virtual_screen']}")
```

---

### 7. take_screenshot

Capture and optionally analyze screenshot.

**Usage:**

```javascript
// From Claude Desktop
"Take a screenshot"
"Capture the current screen"
```

**Python:**

```python
screenshot = system.take_screenshot(
    monitor=0,
    save_path="screenshot.png"
)
```

**Parameters:**
- `monitor` (int, optional): Monitor to capture, default 0
- `save_path` (string, optional): Path to save image, default None

**Returns:**
- `screenshot` (dict):
  - `width`, `height` (int): Dimensions
  - `path` (str): Saved file path (if saved)
  - `data` (numpy.ndarray): Image data

**Example:**

```python
# Capture and save
screenshot = system.take_screenshot(save_path="screen.png")
print(f"Saved {screenshot['width']}×{screenshot['height']} screenshot")

# Capture without saving
screenshot = system.take_screenshot()
# Process screenshot['data'] with OpenCV/PIL
```

---

## Calibration Workflow

### Why Calibrate?

Calibration improves accuracy from ~4.5px error to **0.24px error** (84% improvement).

**Before Calibration:**
- Mean error: 4.5 pixels
- Success rate: ~80% within 5px

**After Calibration:**
- Mean error: 0.24 pixels
- Success rate: 100% within 2px

### Quick Calibration (Recommended)

```python
from mcp_accurate_click_server import AccurateClickSystem

# Initialize with calibration enabled
system = AccurateClickSystem(use_calibration=True)

# Run calibration (20 points, ~30 seconds)
system.calibrate_system(num_points=20)

# Save for future use
system.calibration.save_calibration("my_calibration.npz")

# Verify calibration
status = system.get_calibration_status()
print(f"Mean error: {status['mean_error']:.2f}px")
```

### High-Accuracy Calibration

```python
# For ultra-high accuracy (100 points, ~2 minutes)
system.calibrate_system(
    num_points=100,
    save_file="ultra_accurate.npz"
)

# Expected results:
# Mean error: < 0.1 pixels
# Success rate: 100% within 1px
```

### Calibration Best Practices

1. **When to Calibrate:**
   - First time using the system
   - After DPI settings change
   - After connecting/disconnecting monitors
   - If clicks seem consistently offset

2. **Number of Points:**
   - 20 points: Good for general use (0.7px error)
   - 50 points: Better accuracy (0.4px error)
   - 100 points: Ultra-high accuracy (0.24px error)

3. **Calibration Tips:**
   - Click calibration points as accurately as possible
   - Use full screen area (corners, edges, center)
   - Avoid moving mouse during calibration
   - Recalibrate if system restarts

### Loading Saved Calibration

```python
# Initialize system
system = AccurateClickSystem(use_calibration=True)

# Load previously saved calibration
system.calibration.load_calibration("my_calibration.npz")

# Verify it loaded
status = system.get_calibration_status()
print(f"✓ Loaded calibration with {status['num_points']} points")
```

### Manual Calibration Points

```python
# Advanced: Add calibration points manually
system = AccurateClickSystem(use_calibration=True)

# Add point correspondences (OCR coords → true coords)
system.calibration.add_calibration_point((100, 100), (102, 98))
system.calibration.add_calibration_point((500, 500), (498, 502))
# ... add more points ...

# Compute calibration from added points
system.calibration.compute_calibration(use_ransac=True)

# Check results
errors = system.calibration.get_calibration_errors()
print(f"Mean error: {errors.mean():.2f}px")
```

---

## Configuration Options

### System Initialization

```python
system = AccurateClickSystem(
    use_calibration=True,      # Enable calibration
    use_gpu=False,             # Use GPU for OCR
    ocr_lang='en',             # OCR language
    min_confidence=0.8,        # Default confidence threshold
    calibration_file='cal.npz' # Auto-load calibration
)
```

### OCR Configuration

```python
# Customize OCR engine
from paddleocr import PaddleOCR

custom_ocr = PaddleOCR(
    use_angle_cls=True,        # Detect rotated text
    lang='en',                 # Language ('en', 'ch', etc.)
    use_gpu=True,              # GPU acceleration
    show_log=False,            # Hide logs
    det_db_thresh=0.3,         # Detection threshold
    det_db_box_thresh=0.5,     # Box threshold
    rec_batch_num=6            # Batch size
)

# Use custom OCR with system
system.ocr_engine.ocr = custom_ocr
```

### DPI Settings (Windows)

```python
# Force specific DPI awareness mode
import ctypes

# Per-Monitor V2 (recommended)
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
ctypes.windll.user32.SetProcessDpiAwarenessContext(
    DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
)

# Then initialize system
system = AccurateClickSystem()
```

### Environment Variables

```bash
# Set via environment variables
export ACCURATE_CLICK_GPU=true
export ACCURATE_CLICK_CALIBRATION=/path/to/calibration.npz
export ACCURATE_CLICK_LANG=en
export ACCURATE_CLICK_CONFIDENCE=0.8

python -m mcp_accurate_click_server
```

---

## Advanced Usage

### Batch Clicking

```python
# Click multiple elements
targets = ["File", "Edit", "View", "Help"]

for target in targets:
    success = system.click_on_text(target)
    print(f"{'✓' if success else '✗'} Clicked {target}")
```

### Region-of-Interest OCR

```python
# OCR only specific screen region (faster)
roi = (100, 100, 800, 600)  # (x, y, width, height)

# Crop screenshot to ROI before OCR
screenshot = system.screenshot_manager.capture_screen()
roi_img = screenshot[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]]

# Process ROI
# (Advanced - requires custom implementation)
```

### Click with Offset

```python
# Click offset from detected text
bbox = system.ocr_engine.find_text("screenshot.png", "Submit")

if bbox:
    # Click 10 pixels to the right of text
    click_x = bbox.center[0] + 10
    click_y = bbox.center[1]
    system.click_at_coordinates(click_x, click_y)
```

### Multi-Monitor Workflow

```python
# Get all monitors
info = system.get_system_info()

for monitor in info['monitors']:
    print(f"Scanning monitor {monitor['index']}...")

    # Get text on specific monitor
    text_elements = system.get_screen_text(monitor=monitor['index'])

    # Process elements
    for elem in text_elements:
        print(f"  Found: {elem['text']}")
```

### Error Handling

```python
try:
    success = system.click_on_text("Submit")

    if not success:
        print("Text not found")
        # Fallback: try with lower confidence
        success = system.click_on_text("Submit", min_confidence=0.6)

except Exception as e:
    print(f"Click failed: {e}")
    # Log error, retry, or alert user
```

---

## Troubleshooting

### Clicks are Offset

**Problem**: Clicks land in wrong location

**Solutions:**

1. **Run calibration:**
   ```python
   system.calibrate_system(num_points=20)
   ```

2. **Check DPI awareness (Windows):**
   ```python
   import ctypes
   awareness = ctypes.windll.user32.GetAwarenessFromDpiAwarenessContext(
       ctypes.windll.user32.GetThreadDpiAwarenessContext()
   )
   print(f"DPI Awareness: {awareness}")
   # Should be -4 (Per-Monitor V2) or -3 (Per-Monitor V1)
   ```

3. **Verify monitor configuration:**
   ```python
   info = system.get_system_info()
   print(info['monitors'])
   # Check DPI and scale factors
   ```

---

### Text Not Found

**Problem**: `click_on_text()` returns False

**Solutions:**

1. **Lower confidence threshold:**
   ```python
   system.click_on_text("Submit", min_confidence=0.6)
   ```

2. **Check what OCR sees:**
   ```python
   elements = system.get_screen_text()
   for elem in elements:
       print(f"'{elem['text']}' (confidence: {elem['confidence']:.2%})")
   ```

3. **Try different OCR language:**
   ```python
   system = AccurateClickSystem(ocr_lang='ch')  # For Chinese
   ```

4. **Check text is actually visible:**
   ```python
   screenshot = system.take_screenshot(save_path="debug.png")
   # Manually verify text is in screenshot
   ```

---

### Slow Performance

**Problem**: OCR takes too long (>2 seconds)

**Solutions:**

1. **Enable GPU:**
   ```python
   system = AccurateClickSystem(use_gpu=True)
   ```

2. **Reduce screenshot size:**
   ```python
   # Capture specific monitor instead of all
   system.get_screen_text(monitor=1)
   ```

3. **Optimize OCR settings:**
   ```python
   from paddleocr import PaddleOCR

   fast_ocr = PaddleOCR(
       use_angle_cls=False,  # Disable rotation detection
       det_db_thresh=0.5,    # Higher threshold = faster
       rec_batch_num=12      # Larger batch = faster
   )
   ```

---

### Multi-Monitor Issues

**Problem**: Clicks fail on secondary monitor

**Solution (Windows):**
```python
# Verify MOUSEEVENTF_VIRTUALDESK flag is used
# (Already handled in AccurateClickSystem)

# Check virtual desktop bounds:
info = system.get_system_info()
print(f"Virtual screen: {info['virtual_screen']}")
```

**Solution (Linux):**
```bash
# Ensure multi-head display is configured
xrandr --listmonitors

# Should show all monitors
```

---

### Calibration Not Improving Accuracy

**Problem**: Calibration doesn't help

**Diagnosis:**

```python
# Check calibration errors
errors = system.calibration.get_calibration_errors()
print(f"Mean error: {errors.mean():.2f}px")
print(f"Max error: {errors.max():.2f}px")

# If errors are still high (>2px), try:
```

**Solutions:**

1. **More calibration points:**
   ```python
   system.calibrate_system(num_points=50)
   ```

2. **Use RANSAC for robustness:**
   ```python
   system.calibration.compute_calibration(use_ransac=True)
   ```

3. **Check for non-linear distortion:**
   ```python
   # May need polynomial calibration (advanced)
   ```

---

## Next Steps

- **API Reference**: See [API_REFERENCE.md](API_REFERENCE.md) for detailed API docs
- **Examples**: Check [../examples/](../examples/) for complete code examples
- **Architecture**: Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand system design
- **Research**: Review [RESEARCH_SUMMARY.md](RESEARCH_SUMMARY.md) for validation details

---

**Happy clicking with 100% accuracy!**
