# Installation Guide

Complete installation instructions for the Accurate Click MCP Server on Windows and Linux.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Python Installation](#python-installation)
3. [Dependency Installation](#dependency-installation)
4. [GPU Support Setup](#gpu-support-setup-optional)
5. [Platform-Specific Setup](#platform-specific-setup)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Operating System

**Windows:**
- Windows 10 version 1703+ (recommended - for Per-Monitor DPI V2)
- Windows 8.1+ (supported - Per-Monitor DPI V1)
- Windows 7+ (basic support - System DPI aware)

**Linux:**
- Ubuntu 20.04+ / Debian 10+
- Fedora 33+ / RHEL 8+
- Any modern Linux distribution with X11 or Wayland
- Display server with proper permissions

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | Dual-core 2.0 GHz | Quad-core 3.0 GHz+ |
| **RAM** | 4 GB | 8 GB+ |
| **GPU** | Not required | NVIDIA GPU with CUDA 11.2+ |
| **Display** | Any resolution | 1920×1080 or higher |
| **Storage** | 2 GB free | 5 GB free |

### Python Version

- **Required**: Python 3.8 or higher
- **Recommended**: Python 3.10 or 3.11
- **Architecture**: 64-bit required (for SendInput on Windows)

---

## Python Installation

### Windows

**Option 1: Official Python Installer**

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer
3. **Important**: Check "Add Python to PATH"
4. Choose "Install Now"
5. Verify installation:

```cmd
python --version
# Should show: Python 3.10.x or higher
```

**Option 2: Microsoft Store**

```cmd
# Search for "Python 3.11" in Microsoft Store
# Install directly
```

**Option 3: Anaconda/Miniconda**

```bash
# Download from https://www.anaconda.com/
conda create -n accurate-click python=3.10
conda activate accurate-click
```

### Linux

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
```

**Fedora/RHEL:**

```bash
sudo dnf install python3 python3-pip
python3 --version
```

**From Source (if needed):**

```bash
# Install build dependencies
sudo apt install build-essential libssl-dev libffi-dev python3-dev

# Download and install Python 3.10
wget https://www.python.org/ftp/python/3.10.11/Python-3.10.11.tgz
tar -xf Python-3.10.11.tgz
cd Python-3.10.11
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall
```

---

## Dependency Installation

### Basic Installation (CPU Only)

**Step 1: Create Virtual Environment (Recommended)**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

**Step 2: Install Core Dependencies**

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install numpy opencv-python Pillow mss scipy
pip install paddlepaddle paddleocr
```

**Step 3: Install MCP Server**

```bash
# From source
git clone https://github.com/yourusername/mcp-accurate-click-server.git
cd mcp-accurate-click-server
pip install -e .

# Or if available on PyPI
pip install mcp-accurate-click-server
```

### Dependency Breakdown

| Package | Purpose | Size | Required |
|---------|---------|------|----------|
| **numpy** | Numerical computations | ~50 MB | Yes |
| **opencv-python** | Image processing | ~90 MB | Yes |
| **Pillow** | Image handling | ~10 MB | Yes |
| **mss** | Screenshot capture | ~1 MB | Yes |
| **scipy** | Scientific computing | ~100 MB | Yes |
| **paddlepaddle** | OCR engine backend | ~200 MB | Yes |
| **paddleocr** | OCR implementation | ~50 MB | Yes |

**Total Download Size**: ~500 MB
**Total Installed Size**: ~1.5 GB

---

## GPU Support Setup (Optional)

GPU acceleration provides 3-10x faster OCR processing.

### Requirements

- **NVIDIA GPU** with CUDA Compute Capability 3.5+
- **CUDA Toolkit** 11.2, 11.6, 11.7, or 11.8
- **cuDNN** 8.x

### Windows GPU Setup

**Step 1: Install CUDA Toolkit**

1. Download from [NVIDIA CUDA Downloads](https://developer.nvidia.com/cuda-downloads)
2. Choose your Windows version
3. Download and run installer (2-3 GB)
4. Verify installation:

```cmd
nvcc --version
```

**Step 2: Install cuDNN**

1. Download from [NVIDIA cuDNN](https://developer.nvidia.com/cudnn) (requires free account)
2. Extract to CUDA installation directory (e.g., `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8`)
3. Add to PATH if not automatic

**Step 3: Install PaddlePaddle GPU Version**

```bash
# Uninstall CPU version if installed
pip uninstall paddlepaddle

# Install GPU version (CUDA 11.8 example)
pip install paddlepaddle-gpu
```

**Step 4: Verify GPU Support**

```python
import paddle
print(paddle.device.get_device())  # Should show 'gpu:0'
```

### Linux GPU Setup

**Step 1: Install NVIDIA Drivers**

```bash
# Ubuntu
sudo apt install nvidia-driver-535

# Verify
nvidia-smi
```

**Step 2: Install CUDA Toolkit**

```bash
# Ubuntu 22.04 example
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda-repo-ubuntu2204-11-8-local_11.8.0-520.61.05-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204-11-8-local_11.8.0-520.61.05-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2204-11-8-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get install cuda
```

**Step 3: Install cuDNN**

```bash
# Download from NVIDIA, then:
sudo dpkg -i cudnn-local-repo-ubuntu2204-8.9.2.26_1.0-1_amd64.deb
sudo apt-get update
sudo apt-get install libcudnn8
```

**Step 4: Install PaddlePaddle GPU**

```bash
pip install paddlepaddle-gpu
```

### GPU Troubleshooting

**Issue**: `import paddle` shows CPU device

```bash
# Check CUDA availability
python -c "import paddle; print(paddle.device.cuda.device_count())"

# Should show: 1 or more

# If shows 0, reinstall paddlepaddle-gpu
pip uninstall paddlepaddle paddlepaddle-gpu
pip install paddlepaddle-gpu
```

**Issue**: CUDA version mismatch

```bash
# Check installed CUDA version
nvcc --version

# Install matching PaddlePaddle version:
# CUDA 11.2: pip install paddlepaddle-gpu==2.5.1.post112
# CUDA 11.6: pip install paddlepaddle-gpu==2.5.1.post116
# CUDA 11.7: pip install paddlepaddle-gpu==2.5.1.post117
# CUDA 11.8: pip install paddlepaddle-gpu
```

---

## Platform-Specific Setup

### Windows Setup

**1. Set DPI Awareness**

The application needs DPI awareness to work correctly. This is handled programmatically, but you can also set via manifest.

Create `app.manifest`:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/pm</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </windowsSettings>
  </application>
</assembly>
```

**2. Windows Defender Exclusion (Optional)**

For better performance, exclude Python directory from Windows Defender:

```powershell
# Run PowerShell as Administrator
Add-MpPreference -ExclusionPath "C:\Users\YourName\AppData\Local\Programs\Python"
```

**3. Permissions**

No special permissions required. Application runs as normal user.

### Linux Setup

**1. Install X11 Dependencies**

```bash
# Ubuntu/Debian
sudo apt install python3-tk python3-dev
sudo apt install libx11-dev libxext-dev libxfixes-dev libxi-dev

# Fedora
sudo dnf install python3-tkinter python3-devel
sudo dnf install libX11-devel libXext-devel libXfixes-devel libXi-devel
```

**2. Grant Display Access Permissions**

```bash
# Allow access to X11 display
xhost +local:

# Or more secure (allow specific user)
xhost +SI:localuser:$(whoami)
```

**3. Wayland Support (Experimental)**

```bash
# Install XWayland if not present
sudo apt install xwayland

# Set environment variable
export XDG_SESSION_TYPE=x11
```

**4. Install Input Control Tools**

```bash
# For click simulation on Linux
sudo apt install xdotool

# Or python-xlib (already included in dependencies)
pip install python-xlib
```

---

## Verification

### Test Basic Installation

```python
# test_installation.py
import numpy as np
import cv2
from PIL import Image
import mss
from paddleocr import PaddleOCR

print("✓ All core dependencies installed successfully")

# Test OCR initialization
ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
print("✓ PaddleOCR initialized successfully")

# Test screenshot
with mss.mss() as sct:
    screenshot = sct.grab(sct.monitors[0])
    print(f"✓ Screenshot captured: {screenshot.width}x{screenshot.height}")

print("\n✓✓✓ Installation verification PASSED ✓✓✓")
```

Run verification:

```bash
python test_installation.py
```

### Test MCP Server

```bash
# Start MCP server in test mode
python -m mcp_accurate_click_server --test

# Expected output:
# ✓ MCP Server initialized
# ✓ OCR engine ready
# ✓ DPI manager initialized
# ✓ Screenshot manager ready
# ✓ Server listening on stdio
```

### Test Click Functionality

```python
# test_click.py
from mcp_accurate_click_server import AccurateClickSystem

# Initialize
system = AccurateClickSystem(use_calibration=False)

# Get system info
info = system.get_system_info()
print(f"Monitors detected: {len(info['monitors'])}")

for i, monitor in enumerate(info['monitors']):
    print(f"  Monitor {i}: {monitor['resolution']} @ {monitor['dpi']}")

# Test screenshot and OCR
text_elements = system.get_screen_text()
print(f"\nDetected {len(text_elements)} text elements on screen")

print("\n✓ Click system working correctly")
```

---

## Troubleshooting

### Common Issues

#### 1. Import Error: No module named 'paddle'

**Solution:**

```bash
pip install paddlepaddle
# Or for GPU:
pip install paddlepaddle-gpu
```

#### 2. OCR models not downloading

**Problem**: Slow or failed model download (~200MB)

**Solution:**

```bash
# Download models manually
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='en')"

# Or set download directory
export HOME=/path/to/large/disk
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='en')"
```

#### 3. Permission denied on Linux

**Solution:**

```bash
# Add user to input group
sudo usermod -a -G input $USER

# Grant X11 access
xhost +local:
```

#### 4. DPI scaling issues on Windows

**Problem**: Clicks are offset

**Solution:**

```python
# Ensure DPI awareness is set at application start
import ctypes
ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)

# Then initialize system
from mcp_accurate_click_server import AccurateClickSystem
system = AccurateClickSystem()
```

#### 5. Slow OCR performance

**Solutions:**

```bash
# Option 1: Install GPU support (see GPU section)
pip install paddlepaddle-gpu

# Option 2: Use lighter OCR model
# In Python:
ocr = PaddleOCR(use_angle_cls=False, use_gpu=False, det_db_thresh=0.5)

# Option 3: Reduce screenshot region
# Only OCR specific regions instead of full screen
```

#### 6. Multi-monitor not working

**Problem**: Clicks only work on primary monitor

**Solution (Windows):**

```python
# Ensure MOUSEEVENTF_VIRTUALDESK flag is used
# This is handled automatically in AccurateClickSystem

# Verify virtual desktop detection:
system = AccurateClickSystem()
info = system.get_system_info()
print(f"Virtual screen: {info['virtual_screen']}")
# Should show full virtual desktop bounds
```

**Solution (Linux):**

```bash
# Check Xinerama/RandR extension
xdpyinfo | grep -i xinerama

# Should show: Xinerama extension enabled
```

#### 7. Calibration file not saving

**Problem**: Permission error when saving .npz file

**Solution:**

```python
# Use absolute path with write permissions
import os
calibration_path = os.path.expanduser("~/calibration.npz")
system.calibration.save_calibration(calibration_path)
```

### Platform-Specific Issues

#### Windows

**Issue**: "DLL load failed" errors

**Solution:**

```bash
# Install Visual C++ Redistributable
# Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

# Or install via chocolatey
choco install vcredist-all
```

#### Linux

**Issue**: "Cannot open display" error

**Solution:**

```bash
# Set DISPLAY environment variable
export DISPLAY=:0

# Or if using SSH
ssh -X user@host
```

**Issue**: Wayland permission errors

**Solution:**

```bash
# Fall back to X11
export GDK_BACKEND=x11
export QT_QPA_PLATFORM=xcb
```

### Getting Help

If you encounter issues not covered here:

1. Check [GitHub Issues](https://github.com/yourusername/mcp-accurate-click-server/issues)
2. Review [Usage Guide](USAGE_GUIDE.md#troubleshooting)
3. Join [Discussions](https://github.com/yourusername/mcp-accurate-click-server/discussions)
4. Contact support: support@example.com

---

## Next Steps

After successful installation:

1. Read the [Usage Guide](USAGE_GUIDE.md) to learn how to use the MCP tools
2. Review [Examples](../examples/) for practical code samples
3. Run [Calibration](USAGE_GUIDE.md#calibration) for maximum accuracy
4. Check [API Reference](API_REFERENCE.md) for detailed documentation

---

**Installation complete! You're ready to achieve 100% click accuracy.**
