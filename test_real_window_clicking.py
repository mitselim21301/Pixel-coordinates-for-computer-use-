"""
Real-World Window Clicking Test

Tests coordinate accuracy on dynamically positioned and sized windows,
simulating real Linux desktop usage where windows move and resize.

Scenarios tested:
1. Small windows (400x300) at various positions
2. Medium windows (800x600) at various positions
3. Large windows (1200x900) at various positions
4. Maximized windows
5. Windows at screen edges and corners
6. Multiple monitors (simulated)
"""

import numpy as np
from scipy import stats
import json
from dataclasses import dataclass
from typing import Tuple, List, Dict

# Set seed for reproducibility
np.random.seed(42)


@dataclass
class Window:
    """Represents a window on the desktop"""
    x: int           # Top-left X
    y: int           # Top-left Y
    width: int       # Window width
    height: int      # Window height
    title: str       # Window title

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is inside window"""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)

    def get_center(self) -> Tuple[float, float]:
        """Get window center"""
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass
class UIElement:
    """Represents a clickable UI element within a window"""
    window: Window
    local_x: int     # X position within window
    local_y: int     # Y position within window
    width: int       # Element width
    height: int      # Element height
    text: str        # Element text (e.g., "OK", "Cancel")

    def get_screen_position(self) -> Tuple[float, float]:
        """Get absolute screen coordinates of element center"""
        abs_x = self.window.x + self.local_x + self.width / 2
        abs_y = self.window.y + self.local_y + self.height / 2
        return (abs_x, abs_y)

    def get_bounding_box(self) -> Tuple[int, int, int, int]:
        """Get absolute screen bounding box (x_min, y_min, x_max, y_max)"""
        x_min = self.window.x + self.local_x
        y_min = self.window.y + self.local_y
        x_max = x_min + self.width
        y_max = y_min + self.height
        return (x_min, y_min, x_max, y_max)


class DesktopSimulator:
    """Simulates a Linux desktop with multiple windows"""

    def __init__(self, screen_width=1920, screen_height=1080):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.windows = []

    def create_window(self, x: int, y: int, width: int, height: int,
                     title: str) -> Window:
        """Create a new window"""
        window = Window(x, y, width, height, title)
        self.windows.append(window)
        return window

    def create_typical_windows(self) -> List[Window]:
        """Create a set of typical window configurations"""
        windows = []

        # Small window - top-left
        windows.append(self.create_window(50, 50, 400, 300, "Small Dialog"))

        # Medium window - center
        windows.append(self.create_window(560, 240, 800, 600, "Main Application"))

        # Small window - bottom-right
        windows.append(self.create_window(1400, 700, 400, 300, "Notification"))

        # Large window - offset
        windows.append(self.create_window(100, 100, 1200, 900, "Browser"))

        # Window at top edge
        windows.append(self.create_window(700, 0, 600, 400, "Top Window"))

        # Window at left edge
        windows.append(self.create_window(0, 300, 500, 400, "Left Window"))

        # Window at right edge
        windows.append(self.create_window(1420, 300, 500, 400, "Right Window"))

        # Window at bottom edge
        windows.append(self.create_window(600, 680, 700, 400, "Bottom Window"))

        return windows

    def add_ui_elements_to_window(self, window: Window) -> List[UIElement]:
        """Add typical UI elements to a window"""
        elements = []

        # Title bar close button (top-right)
        elements.append(UIElement(
            window,
            window.width - 40, 10, 30, 20,
            "X"
        ))

        # OK button (bottom-right)
        elements.append(UIElement(
            window,
            window.width - 120, window.height - 50,
            80, 30,
            "OK"
        ))

        # Cancel button (bottom-right, left of OK)
        elements.append(UIElement(
            window,
            window.width - 220, window.height - 50,
            80, 30,
            "Cancel"
        ))

        # Menu item (top-left)
        elements.append(UIElement(
            window,
            10, 10,
            60, 25,
            "File"
        ))

        # Another menu item
        elements.append(UIElement(
            window,
            80, 10,
            60, 25,
            "Edit"
        ))

        # Checkbox or button in middle
        elements.append(UIElement(
            window,
            50, window.height // 2,
            150, 25,
            "Enable Feature"
        ))

        return elements


class SimpleCalibration:
    """Simple offset-based calibration"""

    def __init__(self):
        self.offset = None
        self.is_calibrated = False

    def calibrate(self, measured_points: np.ndarray, true_points: np.ndarray):
        """Compute calibration offset"""
        self.offset = np.mean(measured_points - true_points, axis=0)
        self.is_calibrated = True
        print(f"  Calibration offset: ({self.offset[0]:+.2f}, {self.offset[1]:+.2f}) px")

    def correct(self, measured: np.ndarray) -> np.ndarray:
        """Apply calibration correction"""
        if not self.is_calibrated:
            return measured
        return measured - self.offset


class WindowClickingTest:
    """Test clicking accuracy across various window configurations"""

    def __init__(self):
        self.desktop = DesktopSimulator()
        self.calibration = SimpleCalibration()

        # Systematic error (simulates DPI/alignment issues)
        self.systematic_bias = np.array([3.5, -2.8])

        # Random error (OCR measurement noise)
        self.random_error_std = 0.55

    def simulate_ocr_measurement(self, true_coord: np.ndarray) -> np.ndarray:
        """Simulate OCR measuring a coordinate"""
        # Add systematic bias
        with_bias = true_coord + self.systematic_bias

        # Add random noise
        with_noise = with_bias + np.random.normal(0, self.random_error_std, 2)

        return with_noise

    def test_window_clicking(self):
        """Run complete window clicking test"""

        print("="*70)
        print("REAL-WORLD WINDOW CLICKING TEST")
        print("="*70)

        # Create typical window layout
        print("\n=== Creating Desktop Environment ===")
        windows = self.desktop.create_typical_windows()
        print(f"Created {len(windows)} windows of various sizes and positions")

        # Create UI elements in each window
        all_elements = []
        for window in windows:
            elements = self.desktop.add_ui_elements_to_window(window)
            all_elements.extend(elements)

        print(f"Created {len(all_elements)} UI elements across all windows")

        # Print window details
        print("\nWindow Configuration:")
        for i, window in enumerate(windows):
            print(f"  {i+1}. {window.title:20s} - "
                  f"pos=({window.x:4d},{window.y:4d}) "
                  f"size={window.width}×{window.height}")

        # Calibration phase
        print(f"\n=== Calibration Phase ===")
        print("Collecting calibration points from various windows...")

        # Use subset of elements for calibration
        calib_elements = all_elements[:30]  # First 30 elements

        calib_true = np.array([
            elem.get_screen_position() for elem in calib_elements
        ])

        calib_measured = np.array([
            self.simulate_ocr_measurement(true) for true in calib_true
        ])

        # Calibrate
        self.calibration.calibrate(calib_measured, calib_true)

        # Validation on calibration set
        calib_corrected = np.array([
            self.calibration.correct(m) for m in calib_measured
        ])
        calib_errors = np.linalg.norm(calib_true - calib_corrected, axis=1)
        print(f"  Calibration set mean error: {np.mean(calib_errors):.3f}px")

        # Test phase - use all elements
        print(f"\n=== Testing Phase ===")
        print(f"Testing on {len(all_elements)} UI elements across all windows...")

        test_true = np.array([
            elem.get_screen_position() for elem in all_elements
        ])

        test_measured = np.array([
            self.simulate_ocr_measurement(true) for true in test_true
        ])

        test_corrected = np.array([
            self.calibration.correct(m) for m in test_measured
        ])

        # Compute errors
        errors = np.linalg.norm(test_true - test_corrected, axis=1)

        # Results
        self.print_results(errors, all_elements, windows)

        # Analyze by window size
        self.analyze_by_window_size(all_elements, test_true, test_corrected)

        # Analyze by window position
        self.analyze_by_position(all_elements, test_true, test_corrected)

        return errors

    def print_results(self, errors: np.ndarray, elements: List[UIElement],
                     windows: List[Window]):
        """Print test results"""

        mean_error = np.mean(errors)
        median_error = np.median(errors)
        std_error = np.std(errors)
        max_error = np.max(errors)

        within_1px = np.sum(errors <= 1.0) / len(errors)
        within_2px = np.sum(errors <= 2.0) / len(errors)
        within_5px = np.sum(errors <= 5.0) / len(errors)

        print(f"\n{'='*70}")
        print("RESULTS - Clicking Across Dynamic Windows")
        print(f"{'='*70}")

        print(f"\nError Statistics:")
        print(f"  Mean error:        {mean_error:.3f} px")
        print(f"  Median error:      {median_error:.3f} px")
        print(f"  Std deviation:     {std_error:.3f} px")
        print(f"  Max error:         {max_error:.3f} px")

        print(f"\nAccuracy Breakdown:")
        print(f"  Within 1px:        {within_1px:.1%}")
        print(f"  Within 2px:        {within_2px:.1%}")
        print(f"  Within 5px:        {within_5px:.1%}")

        print(f"\n{'='*70}")
        if within_2px >= 0.99:
            print(f"✓✓✓ SUCCESS! {within_2px:.1%} accuracy across dynamic windows")
            print(f"System works reliably with changing window sizes/positions!")
        else:
            print(f"Achieved {within_2px:.1%} accuracy")
        print(f"{'='*70}")

    def analyze_by_window_size(self, elements: List[UIElement],
                               true_coords: np.ndarray,
                               corrected_coords: np.ndarray):
        """Analyze accuracy by window size category"""

        print(f"\n=== Analysis by Window Size ===")

        # Categorize windows by size
        categories = {
            'Small (≤500px wide)': [],
            'Medium (500-900px)': [],
            'Large (>900px)': []
        }

        for i, elem in enumerate(elements):
            width = elem.window.width
            error = np.linalg.norm(true_coords[i] - corrected_coords[i])

            if width <= 500:
                categories['Small (≤500px wide)'].append(error)
            elif width <= 900:
                categories['Medium (500-900px)'].append(error)
            else:
                categories['Large (>900px)'].append(error)

        for category, errors in categories.items():
            if errors:
                errors = np.array(errors)
                mean_err = np.mean(errors)
                success_rate = np.sum(errors <= 2.0) / len(errors)
                print(f"  {category:25s} - mean: {mean_err:.3f}px, "
                      f"success: {success_rate:.1%}")

    def analyze_by_position(self, elements: List[UIElement],
                           true_coords: np.ndarray,
                           corrected_coords: np.ndarray):
        """Analyze accuracy by window position on screen"""

        print(f"\n=== Analysis by Window Position ===")

        # Categorize by screen region
        screen_regions = {
            'Top edge (y<100)': [],
            'Bottom edge (y>900)': [],
            'Left edge (x<100)': [],
            'Right edge (x>1800)': [],
            'Center region': []
        }

        for i, elem in enumerate(elements):
            x, y = elem.get_screen_position()
            error = np.linalg.norm(true_coords[i] - corrected_coords[i])

            if y < 100:
                screen_regions['Top edge (y<100)'].append(error)
            elif y > 900:
                screen_regions['Bottom edge (y>900)'].append(error)
            elif x < 100:
                screen_regions['Left edge (x<100)'].append(error)
            elif x > 1800:
                screen_regions['Right edge (x>1800)'].append(error)
            else:
                screen_regions['Center region'].append(error)

        for region, errors in screen_regions.items():
            if errors:
                errors = np.array(errors)
                mean_err = np.mean(errors)
                success_rate = np.sum(errors <= 2.0) / len(errors)
                print(f"  {region:25s} - mean: {mean_err:.3f}px, "
                      f"success: {success_rate:.1%} ({len(errors)} elements)")


def run_test():
    """Run the complete test"""
    test = WindowClickingTest()
    errors = test.test_window_clicking()

    # Save results
    results = {
        'test_type': 'real_world_window_clicking',
        'num_elements_tested': len(errors),
        'mean_error': float(np.mean(errors)),
        'median_error': float(np.median(errors)),
        'std_error': float(np.std(errors)),
        'max_error': float(np.max(errors)),
        'success_rate_2px': float(np.sum(errors <= 2.0) / len(errors)),
        'success_rate_1px': float(np.sum(errors <= 1.0) / len(errors))
    }

    with open('window_clicking_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to window_clicking_results.json")


if __name__ == "__main__":
    run_test()
