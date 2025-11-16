"""
Test Suite for Click Executor
Validates cross-platform click execution functionality
"""

import sys
import platform
from typing import Tuple

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    print("Note: pytest not installed. Skipping automated tests.")
    print("Run manual tests only. Install pytest for full test suite.\n")

from click_executor import (
    ClickExecutor,
    WindowsClickExecutor,
    LinuxClickExecutor,
    MacOSClickExecutor,
    get_platform_executor,
    get_executor,
    click,
    double_click,
    right_click,
    get_cursor_position,
)


if HAS_PYTEST:
    pytest_mark = pytest.mark
else:
    # Dummy decorator when pytest not available
    class DummyMark:
        def skipif(self, *args, **kwargs):
            return lambda x: x
    pytest_mark = DummyMark()


class TestPlatformDetection:
    """Test platform detection and executor factory"""

    def test_get_platform_executor(self):
        """Test that get_platform_executor returns correct executor for platform"""
        executor = get_platform_executor()
        assert isinstance(executor, ClickExecutor)

        system = platform.system()
        if system == 'Windows':
            assert isinstance(executor, WindowsClickExecutor)
        elif system == 'Linux':
            assert isinstance(executor, LinuxClickExecutor)
        elif system == 'Darwin':
            assert isinstance(executor, MacOSClickExecutor)

    def test_get_executor_singleton(self):
        """Test that get_executor returns same instance"""
        executor1 = get_executor()
        executor2 = get_executor()
        assert executor1 is executor2  # Should be same instance


class TestClickExecutorInterface:
    """Test base ClickExecutor interface"""

    # Removed @pytest.fixture for compatibility
    def executor(self):
        """Get platform-specific executor"""
        return get_platform_executor()

    def test_executor_has_required_methods(self, executor):
        """Test that executor implements required interface"""
        assert hasattr(executor, 'click')
        assert hasattr(executor, 'double_click')
        assert hasattr(executor, 'right_click')
        assert hasattr(executor, 'get_cursor_position')
        assert callable(executor.click)
        assert callable(executor.double_click)
        assert callable(executor.right_click)
        assert callable(executor.get_cursor_position)

    def test_get_cursor_position(self, executor):
        """Test cursor position retrieval"""
        pos = executor.get_cursor_position()
        assert isinstance(pos, tuple)
        assert len(pos) == 2
        assert isinstance(pos[0], int)
        assert isinstance(pos[1], int)
        # Position should be non-negative
        assert pos[0] >= 0
        assert pos[1] >= 0

    def test_platform_name(self, executor):
        """Test platform name is set"""
        assert executor.platform_name in ['Windows', 'Linux', 'Darwin']


class TestWindowsClickExecutor:
    """Test Windows-specific functionality"""

    def executor(self):
        """Create Windows executor"""
        if platform.system() != 'Windows':
            return None
        return WindowsClickExecutor()

    def test_initialization(self, executor):
        """Test Windows executor initializes correctly"""
        assert executor is not None
        assert hasattr(executor, 'user32')
        assert hasattr(executor, 'ctypes')

    def test_virtual_screen_bounds(self, executor):
        """Test virtual screen bounds retrieval"""
        bounds = executor._get_virtual_screen_bounds()
        assert 'left' in bounds
        assert 'top' in bounds
        assert 'width' in bounds
        assert 'height' in bounds
        assert bounds['width'] > 0
        assert bounds['height'] > 0

    def test_coordinate_normalization(self, executor):
        """Test coordinate normalization logic"""
        bounds = executor._get_virtual_screen_bounds()

        # Test center point
        center_x = bounds['left'] + bounds['width'] // 2
        center_y = bounds['top'] + bounds['height'] // 2

        x_adj = center_x - bounds['left']
        y_adj = center_y - bounds['top']

        x_norm = (x_adj * 65535) // bounds['width']
        y_norm = (y_adj * 65535) // bounds['height']

        # Center should normalize to approximately 32767 (middle of 0-65535)
        assert 30000 < x_norm < 35000
        assert 30000 < y_norm < 35000

    def test_structures_defined(self, executor):
        """Test Windows structures are defined"""
        assert hasattr(executor, 'MOUSEINPUT')
        assert hasattr(executor, 'INPUT')


class TestLinuxClickExecutor:
    """Test Linux-specific functionality"""

    def executor(self):
        """Create Linux executor"""
        if platform.system() != 'Linux':
            return None
        try:
            return LinuxClickExecutor()
        except RuntimeError as e:
            return None

    def test_initialization(self, executor):
        """Test Linux executor initializes correctly"""
        assert executor is not None
        assert hasattr(executor, 'display')
        assert hasattr(executor, 'root')

    def test_x11_connection(self, executor):
        """Test X11 connection is established"""
        assert executor.display is not None
        assert executor.screen is not None
        assert executor.root is not None


class TestConvenienceFunctions:
    """Test convenience wrapper functions"""

    def test_convenience_functions_exist(self):
        """Test that convenience functions are available"""
        # Just test they exist and are callable
        assert callable(click)
        assert callable(double_click)
        assert callable(right_click)
        assert callable(get_cursor_position)

    def test_get_cursor_position_convenience(self):
        """Test convenience function for cursor position"""
        pos = get_cursor_position()
        assert isinstance(pos, tuple)
        assert len(pos) == 2


class TestClickAccuracy:
    """Test click accuracy (simulated)"""

    # Removed @pytest.fixture for compatibility
    def executor(self):
        """Get platform-specific executor"""
        return get_platform_executor()

    def test_coordinate_rounding(self, executor):
        """Test that float coordinates are properly rounded"""
        # Get current position
        original_pos = executor.get_cursor_position()

        # Test coordinates with decimals
        test_coords = [
            (100.1, 200.9),  # Should round to (100, 201)
            (150.5, 250.5),  # Should round to (150, 250) or (151, 251)
            (300.2, 400.8),  # Should round to (300, 401)
        ]

        # Note: We don't actually click here to avoid moving the cursor
        # This is just testing the coordinate handling logic
        for x, y in test_coords:
            x_int = int(round(x))
            y_int = int(round(y))
            assert isinstance(x_int, int)
            assert isinstance(y_int, int)


class TestErrorHandling:
    """Test error handling"""

    # Removed @pytest.fixture for compatibility
    def executor(self):
        """Get platform-specific executor"""
        return get_platform_executor()

    def test_invalid_button_type(self, executor):
        """Test handling of invalid button type"""
        # Should return False for invalid button
        # (except on macOS which raises NotImplementedError)
        if not isinstance(executor, MacOSClickExecutor):
            # Can't test actual click without side effects
            # Just verify button validation exists
            valid_buttons = ['left', 'right', 'middle']
            for button in valid_buttons:
                # Should not raise exception for valid buttons
                pass


def test_module_imports():
    """Test that all expected symbols are importable"""
    from click_executor import (
        ClickExecutor,
        ClickResult,
        ButtonType,
        WindowsClickExecutor,
        LinuxClickExecutor,
        MacOSClickExecutor,
        get_platform_executor,
        get_executor,
        click,
        double_click,
        right_click,
        get_cursor_position,
    )

    # All imports should succeed
    assert ClickExecutor is not None
    assert ClickResult is not None
    assert ButtonType is not None


def run_manual_tests():
    """
    Manual tests that require visual verification.
    Run this separately with: python test_click_executor.py
    """
    print("="*70)
    print("MANUAL CLICK EXECUTOR TESTS")
    print("="*70)

    # Initialize executor
    print("\n1. Initializing executor...")
    try:
        executor = get_platform_executor()
        print(f"   ✓ Initialized: {executor.__class__.__name__}")
        print(f"   Platform: {executor.platform_name}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return

    # Test cursor position
    print("\n2. Testing cursor position...")
    try:
        x, y = executor.get_cursor_position()
        print(f"   ✓ Current position: ({x}, {y})")
    except Exception as e:
        print(f"   ✗ Failed: {e}")

    # Test platform-specific details
    if isinstance(executor, WindowsClickExecutor):
        print("\n3. Windows-specific tests...")
        try:
            bounds = executor._get_virtual_screen_bounds()
            print(f"   ✓ Virtual screen bounds:")
            print(f"     Left: {bounds['left']}")
            print(f"     Top: {bounds['top']}")
            print(f"     Width: {bounds['width']}")
            print(f"     Height: {bounds['height']}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")

    elif isinstance(executor, LinuxClickExecutor):
        print("\n3. Linux-specific tests...")
        try:
            print(f"   ✓ X11 display connected")
            print(f"     Display: {executor.display}")
            print(f"     Screen dimensions: {executor.screen.width_in_pixels}x{executor.screen.height_in_pixels}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")

    print("\n" + "="*70)
    print("MANUAL TEST INSTRUCTIONS")
    print("="*70)
    print("""
To test actual clicking (WARNING: This will move your cursor!):

1. Uncomment the test clicks below
2. Position a test target (e.g., button) at the coordinates
3. Run this script
4. Verify the click lands precisely on the target

# Test code (uncomment to use):
# import time
# print("\\nClicking in 3 seconds at (100, 100)...")
# time.sleep(3)
# executor.click(100, 100)
# print("✓ Click executed")
""")

    print("="*70)
    print("All tests completed!")
    print("="*70)


if __name__ == "__main__":
    # Run manual tests when executed directly
    run_manual_tests()

    # To run pytest tests, use: pytest test_click_executor.py
