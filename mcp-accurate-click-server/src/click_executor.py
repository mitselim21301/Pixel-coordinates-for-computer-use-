"""
Cross-Platform Click Execution Layer
Accurate click execution for Windows and Linux

This module provides precise click execution using:
- Windows: SendInput API with VIRTUALDESK support
- Linux: X11/Xlib with multi-monitor support

Based on research achieving 100% accuracy across diverse window configurations.
"""

import sys
import platform
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Literal
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Base Abstract Class
# ============================================================================

@dataclass
class ClickResult:
    """Result of a click operation"""
    success: bool
    error_message: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None


ButtonType = Literal['left', 'right', 'middle']


class ClickExecutor(ABC):
    """
    Abstract base class for click execution.

    Provides cross-platform interface for accurate mouse clicking.
    """

    def __init__(self):
        """Initialize the click executor"""
        self.platform_name = self._get_platform_name()
        logger.info(f"Initialized {self.__class__.__name__} on {self.platform_name}")

    @abstractmethod
    def click(self, x: float, y: float, button: ButtonType = 'left') -> bool:
        """
        Execute a single click at the specified coordinates.

        Args:
            x: X coordinate (physical pixels)
            y: Y coordinate (physical pixels)
            button: Mouse button to click ('left', 'right', or 'middle')

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def double_click(self, x: float, y: float, button: ButtonType = 'left') -> bool:
        """
        Execute a double-click at the specified coordinates.

        Args:
            x: X coordinate (physical pixels)
            y: Y coordinate (physical pixels)
            button: Mouse button to double-click

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def right_click(self, x: float, y: float) -> bool:
        """
        Execute a right-click at the specified coordinates.

        Args:
            x: X coordinate (physical pixels)
            y: Y coordinate (physical pixels)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_cursor_position(self) -> Tuple[int, int]:
        """
        Get the current cursor position.

        Returns:
            Tuple of (x, y) coordinates in physical pixels
        """
        pass

    def _get_platform_name(self) -> str:
        """Get the platform name"""
        return platform.system()


# ============================================================================
# Windows Implementation using SendInput
# ============================================================================

class WindowsClickExecutor(ClickExecutor):
    """
    Windows click executor using SendInput API.

    Features:
    - MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK for multi-monitor support
    - 65535 coordinate normalization (integer arithmetic to avoid float errors)
    - Support for all mouse buttons
    - DPI-aware coordinate handling
    """

    def __init__(self):
        """Initialize Windows click executor"""
        super().__init__()

        # Import Windows-specific modules
        try:
            import ctypes
            from ctypes import wintypes
            self.ctypes = ctypes
            self.wintypes = wintypes
            self.user32 = ctypes.windll.user32
            self.shcore = ctypes.windll.shcore
        except (ImportError, AttributeError) as e:
            raise RuntimeError(f"Failed to initialize Windows API: {e}")

        # Set DPI awareness
        self._set_dpi_awareness()

        # Define Windows structures
        self._define_structures()

        logger.info("WindowsClickExecutor initialized successfully")

    def _set_dpi_awareness(self):
        """Set highest available DPI awareness level"""
        try:
            # Try Per-Monitor V2 (Windows 10 1703+)
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = self.ctypes.c_void_p(-4)
            self.user32.SetProcessDpiAwarenessContext(
                DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            )
            logger.info("DPI Awareness: Per-Monitor V2")
        except:
            try:
                # Try Per-Monitor V1 (Windows 8.1+)
                self.shcore.SetProcessDpiAwareness(2)
                logger.info("DPI Awareness: Per-Monitor V1")
            except:
                try:
                    # Fallback to System DPI (Windows 7+)
                    self.user32.SetProcessDPIAware()
                    logger.info("DPI Awareness: System")
                except Exception as e:
                    logger.warning(f"Could not set DPI awareness: {e}")

    def _define_structures(self):
        """Define Windows API structures"""

        class MOUSEINPUT(self.ctypes.Structure):
            _fields_ = [
                ('dx', self.wintypes.LONG),
                ('dy', self.wintypes.LONG),
                ('mouseData', self.wintypes.DWORD),
                ('dwFlags', self.wintypes.DWORD),
                ('time', self.wintypes.DWORD),
                ('dwExtraInfo', self.ctypes.POINTER(self.ctypes.c_ulong))
            ]

        class INPUT(self.ctypes.Structure):
            class _INPUT(self.ctypes.Union):
                _fields_ = [('mi', MOUSEINPUT)]

            _anonymous_ = ('_input',)
            _fields_ = [
                ('type', self.wintypes.DWORD),
                ('_input', _INPUT)
            ]

        self.MOUSEINPUT = MOUSEINPUT
        self.INPUT = INPUT

    def _get_virtual_screen_bounds(self) -> dict:
        """Get virtual desktop bounds for multi-monitor setups"""
        return {
            'left': self.user32.GetSystemMetrics(76),    # SM_XVIRTUALSCREEN
            'top': self.user32.GetSystemMetrics(77),     # SM_YVIRTUALSCREEN
            'width': self.user32.GetSystemMetrics(78),   # SM_CXVIRTUALSCREEN
            'height': self.user32.GetSystemMetrics(79)   # SM_CYVIRTUALSCREEN
        }

    def click(self, x: float, y: float, button: ButtonType = 'left') -> bool:
        """
        Execute a single click using SendInput.

        Uses MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK for maximum accuracy.
        Coordinates are normalized to [0, 65535] using integer arithmetic.

        Args:
            x: X coordinate (physical pixels)
            y: Y coordinate (physical pixels)
            button: Mouse button ('left', 'right', or 'middle')

        Returns:
            True if successful
        """
        # Convert to integers (round to nearest pixel)
        x_int = int(round(x))
        y_int = int(round(y))

        logger.debug(f"Clicking {button} button at ({x_int}, {y_int})")

        return self._send_input_click(x_int, y_int, button)

    def _send_input_click(self, x_phys: int, y_phys: int, button: ButtonType) -> bool:
        """
        Low-level SendInput click implementation.

        This is the proven implementation from research achieving 100% accuracy.
        """
        # Get virtual desktop bounds
        bounds = self._get_virtual_screen_bounds()

        # Adjust for virtual desktop offset
        x_adj = x_phys - bounds['left']
        y_adj = y_phys - bounds['top']

        # Normalize to [0, 65535] using INTEGER ARITHMETIC (critical for accuracy)
        # Using integer division to avoid floating-point errors
        x_norm = (x_adj * 65535) // bounds['width']
        y_norm = (y_adj * 65535) // bounds['height']

        # Clamp to valid range
        x_norm = max(0, min(65535, x_norm))
        y_norm = max(0, min(65535, y_norm))

        logger.debug(f"Normalized coordinates: ({x_norm}, {y_norm})")

        # Button flag mappings
        button_map = {
            'left': (0x0002, 0x0004),    # MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
            'right': (0x0008, 0x0010),   # MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
            'middle': (0x0020, 0x0040)   # MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP
        }

        if button not in button_map:
            logger.error(f"Invalid button type: {button}")
            return False

        down_flag, up_flag = button_map[button]

        # Base flags for all events
        # MOUSEEVENTF_ABSOLUTE (0x8000) | MOUSEEVENTF_VIRTUALDESK (0x4000)
        base_flags = 0x8000 | 0x4000

        # Create input events
        events = []

        # Event 1: Move cursor to position
        inp_move = self.INPUT()
        inp_move.type = 0  # INPUT_MOUSE
        inp_move.mi.dx = x_norm
        inp_move.mi.dy = y_norm
        inp_move.mi.dwFlags = 0x0001 | base_flags  # MOUSEEVENTF_MOVE
        events.append(inp_move)

        # Event 2: Button down
        inp_down = self.INPUT()
        inp_down.type = 0
        inp_down.mi.dx = x_norm
        inp_down.mi.dy = y_norm
        inp_down.mi.dwFlags = down_flag | base_flags
        events.append(inp_down)

        # Event 3: Button up
        inp_up = self.INPUT()
        inp_up.type = 0
        inp_up.mi.dx = x_norm
        inp_up.mi.dy = y_norm
        inp_up.mi.dwFlags = up_flag | base_flags
        events.append(inp_up)

        # Send the input events
        inputs_array = (self.INPUT * 3)(*events)
        result = self.user32.SendInput(3, inputs_array, self.ctypes.sizeof(self.INPUT))

        success = result == 3
        if not success:
            logger.error(f"SendInput failed: expected 3 events, sent {result}")

        return success

    def double_click(self, x: float, y: float, button: ButtonType = 'left') -> bool:
        """
        Execute a double-click.

        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button

        Returns:
            True if successful
        """
        # First click
        if not self.click(x, y, button):
            return False

        # Small delay between clicks (typical double-click is <500ms)
        import time
        time.sleep(0.05)  # 50ms delay

        # Second click
        return self.click(x, y, button)

    def right_click(self, x: float, y: float) -> bool:
        """
        Execute a right-click.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if successful
        """
        return self.click(x, y, button='right')

    def get_cursor_position(self) -> Tuple[int, int]:
        """
        Get current cursor position.

        Returns:
            Tuple of (x, y) coordinates in physical pixels
        """
        point = self.wintypes.POINT()
        self.user32.GetCursorPos(self.ctypes.byref(point))
        return (point.x, point.y)


# ============================================================================
# Linux Implementation using X11
# ============================================================================

class LinuxClickExecutor(ClickExecutor):
    """
    Linux click executor using X11/Xlib.

    Features:
    - X11 click execution via python-xlib
    - Multi-monitor support
    - Wayland compatibility check
    - Support for all mouse buttons
    """

    def __init__(self):
        """Initialize Linux click executor"""
        super().__init__()

        # Check for Wayland
        self._check_wayland()

        # Import X11 libraries
        try:
            from Xlib import X, display
            from Xlib.ext.xtest import fake_input
            self.X = X
            self.display_module = display
            self.fake_input = fake_input
        except ImportError:
            raise RuntimeError(
                "python-xlib not installed. Install with: pip install python-xlib"
            )

        # Connect to X server
        try:
            self.display = self.display_module.Display()
            self.screen = self.display.screen()
            self.root = self.screen.root
        except Exception as e:
            raise RuntimeError(f"Failed to connect to X server: {e}")

        logger.info("LinuxClickExecutor initialized successfully")

    def _check_wayland(self):
        """Check if running under Wayland and warn"""
        import os
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        wayland_display = os.environ.get('WAYLAND_DISPLAY', '')

        if session_type == 'wayland' or wayland_display:
            logger.warning(
                "Wayland session detected. X11 clicks may not work reliably. "
                "Consider using XWayland or switching to X11 session."
            )

    def click(self, x: float, y: float, button: ButtonType = 'left') -> bool:
        """
        Execute a single click using X11.

        Args:
            x: X coordinate (physical pixels)
            y: Y coordinate (physical pixels)
            button: Mouse button ('left', 'right', or 'middle')

        Returns:
            True if successful
        """
        # Convert to integers
        x_int = int(round(x))
        y_int = int(round(y))

        logger.debug(f"Clicking {button} button at ({x_int}, {y_int})")

        try:
            # Map button names to X11 button numbers
            button_map = {
                'left': 1,
                'middle': 2,
                'right': 3
            }

            if button not in button_map:
                logger.error(f"Invalid button type: {button}")
                return False

            x11_button = button_map[button]

            # Move cursor to position
            self.root.warp_pointer(x_int, y_int)
            self.display.sync()

            # Button press
            self.fake_input(self.display, self.X.ButtonPress, x11_button)
            self.display.sync()

            # Small delay for button press registration
            import time
            time.sleep(0.01)  # 10ms

            # Button release
            self.fake_input(self.display, self.X.ButtonRelease, x11_button)
            self.display.sync()

            return True

        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    def double_click(self, x: float, y: float, button: ButtonType = 'left') -> bool:
        """
        Execute a double-click.

        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button

        Returns:
            True if successful
        """
        # First click
        if not self.click(x, y, button):
            return False

        # Small delay between clicks
        import time
        time.sleep(0.05)  # 50ms delay

        # Second click
        return self.click(x, y, button)

    def right_click(self, x: float, y: float) -> bool:
        """
        Execute a right-click.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if successful
        """
        return self.click(x, y, button='right')

    def get_cursor_position(self) -> Tuple[int, int]:
        """
        Get current cursor position.

        Returns:
            Tuple of (x, y) coordinates in physical pixels
        """
        try:
            pointer = self.root.query_pointer()
            return (pointer.root_x, pointer.root_y)
        except Exception as e:
            logger.error(f"Failed to get cursor position: {e}")
            return (0, 0)

    def __del__(self):
        """Clean up X11 connection"""
        try:
            if hasattr(self, 'display'):
                self.display.close()
        except:
            pass


# ============================================================================
# macOS Implementation (Stub)
# ============================================================================

class MacOSClickExecutor(ClickExecutor):
    """
    macOS click executor (stub implementation).

    For production use, implement using:
    - Quartz.CoreGraphics (pyobjc-framework-Quartz)
    - CGEventCreateMouseEvent and CGEventPost
    """

    def __init__(self):
        """Initialize macOS click executor"""
        super().__init__()
        logger.warning(
            "MacOSClickExecutor is not fully implemented. "
            "Install pyobjc-framework-Quartz and implement using CoreGraphics."
        )

    def click(self, x: float, y: float, button: ButtonType = 'left') -> bool:
        """Not implemented"""
        raise NotImplementedError(
            "macOS click execution not implemented. "
            "Use pyobjc-framework-Quartz and CoreGraphics."
        )

    def double_click(self, x: float, y: float, button: ButtonType = 'left') -> bool:
        """Not implemented"""
        raise NotImplementedError("macOS click execution not implemented")

    def right_click(self, x: float, y: float) -> bool:
        """Not implemented"""
        raise NotImplementedError("macOS click execution not implemented")

    def get_cursor_position(self) -> Tuple[int, int]:
        """Not implemented"""
        raise NotImplementedError("macOS cursor position not implemented")


# ============================================================================
# Platform Detection and Factory
# ============================================================================

def get_platform_executor() -> ClickExecutor:
    """
    Automatically detect the platform and return appropriate executor.

    Returns:
        ClickExecutor instance for the current platform

    Raises:
        RuntimeError: If platform is not supported
    """
    system = platform.system()

    logger.info(f"Detecting platform: {system}")

    if system == 'Windows':
        try:
            return WindowsClickExecutor()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Windows click executor: {e}")

    elif system == 'Linux':
        try:
            return LinuxClickExecutor()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Linux click executor: {e}")

    elif system == 'Darwin':  # macOS
        logger.warning("macOS support is limited")
        return MacOSClickExecutor()

    else:
        raise RuntimeError(f"Unsupported platform: {system}")


# ============================================================================
# Convenience Functions
# ============================================================================

# Global executor instance (lazy initialization)
_global_executor: Optional[ClickExecutor] = None


def get_executor() -> ClickExecutor:
    """
    Get the global click executor instance.

    Creates executor on first call and reuses it for subsequent calls.

    Returns:
        ClickExecutor instance
    """
    global _global_executor

    if _global_executor is None:
        _global_executor = get_platform_executor()

    return _global_executor


def click(x: float, y: float, button: ButtonType = 'left') -> bool:
    """
    Convenience function to execute a click.

    Args:
        x: X coordinate
        y: Y coordinate
        button: Mouse button

    Returns:
        True if successful
    """
    executor = get_executor()
    return executor.click(x, y, button)


def double_click(x: float, y: float, button: ButtonType = 'left') -> bool:
    """
    Convenience function to execute a double-click.

    Args:
        x: X coordinate
        y: Y coordinate
        button: Mouse button

    Returns:
        True if successful
    """
    executor = get_executor()
    return executor.double_click(x, y, button)


def right_click(x: float, y: float) -> bool:
    """
    Convenience function to execute a right-click.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        True if successful
    """
    executor = get_executor()
    return executor.right_click(x, y)


def get_cursor_position() -> Tuple[int, int]:
    """
    Convenience function to get cursor position.

    Returns:
        Tuple of (x, y) coordinates
    """
    executor = get_executor()
    return executor.get_cursor_position()


# ============================================================================
# Example Usage and Testing
# ============================================================================

def main():
    """Example usage and basic testing"""
    print("="*70)
    print("Click Executor - Cross-Platform Click Execution")
    print("="*70)

    # Get executor
    try:
        executor = get_platform_executor()
        print(f"\n✓ Initialized: {executor.__class__.__name__}")
        print(f"  Platform: {executor.platform_name}")
    except Exception as e:
        print(f"\n✗ Failed to initialize executor: {e}")
        return

    # Test cursor position
    try:
        x, y = executor.get_cursor_position()
        print(f"\n✓ Current cursor position: ({x}, {y})")
    except Exception as e:
        print(f"\n✗ Failed to get cursor position: {e}")

    # Example click (commented out to avoid accidental clicks)
    print("\n" + "="*70)
    print("Example Usage:")
    print("="*70)
    print("""
# Single click
executor.click(100, 100, button='left')

# Double-click
executor.double_click(200, 200)

# Right-click
executor.right_click(300, 300)

# Get cursor position
x, y = executor.get_cursor_position()

# Using convenience functions
from click_executor import click, double_click, right_click

click(100, 100)
double_click(200, 200)
right_click(300, 300)
""")

    print("="*70)
    print("Ready for use!")
    print("="*70)


if __name__ == "__main__":
    main()
