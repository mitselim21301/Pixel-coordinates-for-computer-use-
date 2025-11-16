"""
Example Usage of Coordinate Transformation Pipeline

This script demonstrates how to use the coordinate transformer in real scenarios.
"""

# Mock Windows APIs for cross-platform demonstration
import sys
import ctypes
from unittest.mock import MagicMock, Mock, patch

# Mock Windows APIs before importing coordinate_transformer
if not hasattr(ctypes, 'windll'):
    # Create mock windll
    mock_windll = MagicMock()
    mock_user32 = MagicMock()
    mock_shcore = MagicMock()

    # Configure mocks
    mock_user32.GetSystemMetrics.return_value = 1920  # Default screen width
    mock_user32.MonitorFromPoint.return_value = 1
    mock_user32.EnumDisplayMonitors = MagicMock()

    mock_windll.user32 = mock_user32
    mock_windll.shcore = mock_shcore

    ctypes.windll = mock_windll
    sys.modules['ctypes.wintypes'] = MagicMock()

import numpy as np
from coordinate_transformer import (
    CoordinateTransformer,
    DPIManager,
    OCRFormat,
    quick_transform
)


def example_1_basic_usage():
    """Example 1: Basic usage without calibration"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Usage (No Calibration)")
    print("="*70)

    # Initialize transformer
    transformer = CoordinateTransformer(use_calibration=False)

    # Example OCR output - text bounding box
    bbox = [150, 250, 350, 300]  # "Submit" button at these coordinates

    # Transform to click coordinates
    result = transformer.transform(bbox, OCRFormat.XYXY)

    print(f"\nInput bounding box: {bbox}")
    print(f"Format: XYXY [x_min, y_min, x_max, y_max]")
    print(f"\nTransformation Pipeline:")
    print(f"  Stage 1 (Normalized): {result.stages['stage1_normalized']}")
    print(f"  Stage 2 (Center):     {result.stages['stage2_center']}")
    print(f"  Stage 3 (Scaled):     {result.stages['stage3_scaled']}")
    print(f"  Stage 5 (SendInput):  {result.stages['stage5_normalized']}")
    print(f"\nFinal Click Coordinates:")
    print(f"  Physical pixels: ({result.final_x}, {result.final_y})")
    print(f"  SendInput:       ({result.normalized_x}, {result.normalized_y})")
    print(f"  Validation:      {'PASSED' if result.validation_passed else 'FAILED'}")


def example_2_different_formats():
    """Example 2: Different OCR format conversions"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Different OCR Formats")
    print("="*70)

    transformer = CoordinateTransformer(use_calibration=False)

    # Same region in different formats
    print("\nSame region (100, 200, 300, 400) in different formats:")

    # XYXY format
    bbox_xyxy = [100, 200, 300, 400]
    result_xyxy = transformer.transform(bbox_xyxy, OCRFormat.XYXY)
    print(f"\n  XYXY {bbox_xyxy}")
    print(f"    → Center: ({result_xyxy.final_x}, {result_xyxy.final_y})")

    # XYWH format (x, y, width, height)
    bbox_xywh = [100, 200, 200, 200]
    result_xywh = transformer.transform(bbox_xywh, OCRFormat.XYWH)
    print(f"\n  XYWH {bbox_xywh}")
    print(f"    → Center: ({result_xywh.final_x}, {result_xywh.final_y})")

    # QUAD format (4 corner points)
    bbox_quad = [[100, 200], [300, 200], [300, 400], [100, 400]]
    result_quad = transformer.transform(bbox_quad, OCRFormat.QUAD)
    print(f"\n  QUAD {bbox_quad}")
    print(f"    → Center: ({result_quad.final_x}, {result_quad.final_y})")

    # Normalized format
    bbox_norm = [0.1, 0.2, 0.3, 0.4]
    result_norm = transformer.transform(
        bbox_norm,
        OCRFormat.NORMALIZED,
        screenshot_size=(1000, 1000)
    )
    print(f"\n  NORMALIZED {bbox_norm} (on 1000x1000 image)")
    print(f"    → Center: ({result_norm.final_x}, {result_norm.final_y})")

    print("\n  All formats produce the same center point: (200, 300) ✓")


def example_3_screenshot_scaling():
    """Example 3: Screenshot to screen scaling"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Screenshot Scaling")
    print("="*70)

    transformer = CoordinateTransformer(use_calibration=False)

    # OCR detected text at (150, 150) in a 1280x720 screenshot
    # But actual screen is 1920x1080
    bbox = [100, 100, 200, 200]  # Center at (150, 150)

    print("\nScenario:")
    print("  Screenshot size: 1280 x 720")
    print("  Screen size:     1920 x 1080")
    print("  Detected bbox:   [100, 100, 200, 200]")
    print("  Center in screenshot: (150, 150)")

    result = transformer.transform(
        bbox,
        OCRFormat.XYXY,
        screenshot_size=(1280, 720),
        screen_size=(1920, 1080)
    )

    scale_x = 1920 / 1280
    scale_y = 1080 / 720
    expected_x = 150 * scale_x
    expected_y = 150 * scale_y

    print(f"\nScaling:")
    print(f"  X scale: {scale_x:.2f}x")
    print(f"  Y scale: {scale_y:.2f}x")
    print(f"\nExpected center on screen: ({expected_x:.0f}, {expected_y:.0f})")
    print(f"Actual result:             ({result.final_x}, {result.final_y})")
    print(f"Match: {'✓' if result.final_x == int(expected_x) else '✗'}")


def example_4_calibration():
    """Example 4: Calibration workflow"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Calibration Workflow")
    print("="*70)

    # Create transformer with calibration
    transformer = CoordinateTransformer(use_calibration=True)

    # Simulate calibration data
    # In real scenario, you'd collect these by displaying known positions
    # and recording where OCR detects them
    print("\nGenerating synthetic calibration data...")

    np.random.seed(42)
    n_points = 30

    # True positions (where we displayed markers)
    true_points = np.random.uniform([100, 100], [900, 900], (n_points, 2))

    # Simulated OCR detections with systematic offset and noise
    systematic_offset = np.array([5.0, -3.0])  # Consistent bias
    random_noise = np.random.normal(0, 1.5, (n_points, 2))  # Random error
    measured_points = true_points + systematic_offset + random_noise

    print(f"  Calibration points: {n_points}")
    print(f"  Systematic offset: {systematic_offset}")
    print(f"  Random noise std: 1.5px")

    # Calibrate
    print("\nCalibrating...")
    transformer.calibrate(measured_points, true_points, use_ransac=True)

    # Test calibration on new point
    test_true = np.array([500.0, 500.0])
    test_measured = test_true + systematic_offset + np.array([1.0, -0.5])

    print(f"\nTest point:")
    print(f"  True position:     ({test_true[0]:.1f}, {test_true[1]:.1f})")
    print(f"  Measured (OCR):    ({test_measured[0]:.1f}, {test_measured[1]:.1f})")
    print(f"  Error before:      {np.linalg.norm(test_measured - test_true):.2f}px")

    # Apply calibration
    corrected_x, corrected_y = transformer._apply_calibration(
        test_measured[0], test_measured[1]
    )

    error_after = np.sqrt((corrected_x - test_true[0])**2 +
                         (corrected_y - test_true[1])**2)

    print(f"  Corrected:         ({corrected_x:.1f}, {corrected_y:.1f})")
    print(f"  Error after:       {error_after:.2f}px")
    print(f"  Improvement:       {((np.linalg.norm(test_measured - test_true) - error_after) / np.linalg.norm(test_measured - test_true) * 100):.1f}%")

    # Save calibration
    print("\nSaving calibration...")
    transformer.save_calibration("example_calibration.npz")
    print("  Saved to: example_calibration.npz")


def example_5_dpi_management():
    """Example 5: DPI Manager usage"""
    print("\n" + "="*70)
    print("EXAMPLE 5: DPI Management")
    print("="*70)

    # Note: This will only work correctly on Windows
    # On Linux, it will use mocked values
    try:
        dpi_mgr = DPIManager()

        print(f"\nDPI Awareness Level: {dpi_mgr.awareness_level}")

        # Virtual screen bounds
        bounds = dpi_mgr.get_virtual_screen_bounds()
        print(f"\nVirtual Screen Bounds:")
        print(f"  Left:   {bounds['left']}")
        print(f"  Top:    {bounds['top']}")
        print(f"  Width:  {bounds['width']}")
        print(f"  Height: {bounds['height']}")

        # Coordinate conversion example
        logical_x, logical_y = 100, 100
        print(f"\nCoordinate Conversion Example:")
        print(f"  Logical coordinates:  ({logical_x}, {logical_y})")

        # This would work on Windows with actual DPI info
        # On Linux, it will use default values
        print("  (Note: Actual DPI conversion only works on Windows)")

    except Exception as e:
        print(f"\nDPI Manager not available on this platform: {e}")
        print("This is expected on non-Windows systems.")


def example_6_quick_transform():
    """Example 6: Quick transform convenience function"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Quick Transform")
    print("="*70)

    # Simplest possible usage
    bbox = [100, 200, 300, 400]

    print(f"\nInput: {bbox}")
    x, y = quick_transform(bbox, OCRFormat.XYXY)
    print(f"Output: ({x}, {y})")
    print("\nThis is the fastest way for simple transformations!")


def example_7_validation():
    """Example 7: Coordinate validation"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Validation")
    print("="*70)

    transformer = CoordinateTransformer(use_calibration=False)

    # Valid coordinates
    bbox_valid = [500, 500, 600, 600]
    result_valid = transformer.transform(bbox_valid, OCRFormat.XYXY, validate=True)

    print("\nTest 1: Valid coordinates")
    print(f"  Input: {bbox_valid}")
    print(f"  Validation: {result_valid.validation_passed}")
    print(f"  Error: {result_valid.error_message}")

    # Out of bounds coordinates (would fail validation if screen size provided)
    bbox_invalid = [50000, 50000, 60000, 60000]
    result_invalid = transformer.transform(
        bbox_invalid,
        OCRFormat.XYXY,
        validate=True,
        screen_size=(1920, 1080)
    )

    print("\nTest 2: Out of bounds coordinates")
    print(f"  Input: {bbox_invalid}")
    print(f"  Validation: {result_invalid.validation_passed}")
    print(f"  Error: {result_invalid.error_message}")


def main():
    """Run all examples"""
    print("="*70)
    print("COORDINATE TRANSFORMER - USAGE EXAMPLES")
    print("="*70)
    print("\nThese examples demonstrate the 7-stage transformation pipeline.")
    print("Note: Some features require Windows OS to function fully.")

    # Run examples
    example_1_basic_usage()
    example_2_different_formats()
    example_3_screenshot_scaling()
    example_4_calibration()
    example_5_dpi_management()
    example_6_quick_transform()
    example_7_validation()

    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED")
    print("="*70)
    print("\nFor more details, see:")
    print("  - README.md - Complete documentation")
    print("  - test_coordinate_transformer.py - Test suite")
    print("  - MATHEMATICAL_SOLUTION_SPEC.md - Mathematical foundation")


if __name__ == "__main__":
    main()
