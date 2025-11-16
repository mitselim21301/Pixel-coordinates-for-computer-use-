"""
Test Suite for Coordinate Transformation Pipeline

Tests all 7 stages of the transformation pipeline with mocked Windows APIs
for cross-platform testing.
"""

import numpy as np
import sys
from unittest.mock import Mock, MagicMock, patch
from typing import Tuple

# Mock Windows APIs for cross-platform testing
sys.modules['ctypes.wintypes'] = MagicMock()

# Now we can import our module
from coordinate_transformer import (
    CoordinateTransformer,
    DPIManager,
    OCRFormat,
    normalize_bbox,
    get_center,
    apply_virtual_desktop_offset,
    normalize_for_sendinput,
    BoundingBox,
    TransformationResult
)


class TestCoordinateTransformer:
    """Test suite for CoordinateTransformer"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def assert_equal(self, actual, expected, message=""):
        """Assert equality"""
        if actual == expected:
            self.passed += 1
            return True
        else:
            self.failed += 1
            print(f"  ✗ FAILED: {message}")
            print(f"    Expected: {expected}")
            print(f"    Got: {actual}")
            return False

    def assert_almost_equal(self, actual, expected, tolerance=0.01, message=""):
        """Assert almost equal for floats"""
        if isinstance(actual, tuple):
            diff = max(abs(a - e) for a, e in zip(actual, expected))
        else:
            diff = abs(actual - expected)

        if diff <= tolerance:
            self.passed += 1
            return True
        else:
            self.failed += 1
            print(f"  ✗ FAILED: {message}")
            print(f"    Expected: {expected} (tolerance: {tolerance})")
            print(f"    Got: {actual} (diff: {diff})")
            return False

    def test_stage1_normalize_bbox_xyxy(self):
        """Test Stage 1: XYXY format normalization"""
        print("\nTest: Stage 1 - XYXY Format Normalization")

        bbox = [100, 200, 300, 400]
        result = normalize_bbox(bbox, OCRFormat.XYXY)

        self.assert_equal(result.x_min, 100.0, "x_min")
        self.assert_equal(result.y_min, 200.0, "y_min")
        self.assert_equal(result.x_max, 300.0, "x_max")
        self.assert_equal(result.y_max, 400.0, "y_max")

    def test_stage1_normalize_bbox_xywh(self):
        """Test Stage 1: XYWH format normalization"""
        print("\nTest: Stage 1 - XYWH Format Normalization")

        bbox = [100, 200, 200, 200]  # x, y, width, height
        result = normalize_bbox(bbox, OCRFormat.XYWH)

        self.assert_equal(result.x_min, 100.0, "x_min")
        self.assert_equal(result.y_min, 200.0, "y_min")
        self.assert_equal(result.x_max, 300.0, "x_max (100 + 200)")
        self.assert_equal(result.y_max, 400.0, "y_max (200 + 200)")

    def test_stage1_normalize_bbox_quad(self):
        """Test Stage 1: QUAD format normalization"""
        print("\nTest: Stage 1 - QUAD Format Normalization")

        # Rotated rectangle
        bbox = [[100, 200], [300, 200], [300, 400], [100, 400]]
        result = normalize_bbox(bbox, OCRFormat.QUAD)

        self.assert_equal(result.x_min, 100.0, "x_min")
        self.assert_equal(result.y_min, 200.0, "y_min")
        self.assert_equal(result.x_max, 300.0, "x_max")
        self.assert_equal(result.y_max, 400.0, "y_max")

    def test_stage1_normalize_bbox_normalized(self):
        """Test Stage 1: Normalized format"""
        print("\nTest: Stage 1 - Normalized Format")

        bbox = [0.1, 0.2, 0.3, 0.4]  # Normalized [0, 1]
        result = normalize_bbox(bbox, OCRFormat.NORMALIZED,
                               image_width=1000, image_height=1000)

        self.assert_equal(result.x_min, 100.0, "x_min (0.1 * 1000)")
        self.assert_equal(result.y_min, 200.0, "y_min (0.2 * 1000)")
        self.assert_equal(result.x_max, 300.0, "x_max (0.3 * 1000)")
        self.assert_equal(result.y_max, 400.0, "y_max (0.4 * 1000)")

    def test_stage2_center_calculation(self):
        """Test Stage 2: Center point calculation"""
        print("\nTest: Stage 2 - Center Point Calculation")

        bbox = BoundingBox(100, 200, 300, 400)
        x, y = get_center(bbox)

        self.assert_equal(x, 200.0, "x_center ((100 + 300) / 2)")
        self.assert_equal(y, 300.0, "y_center ((200 + 400) / 2)")

    def test_stage4_virtual_desktop_offset(self):
        """Test Stage 4: Virtual desktop offset"""
        print("\nTest: Stage 4 - Virtual Desktop Offset")

        # Simulate multi-monitor with left monitor positioned at x=-1920
        virtual_bounds = {'left': -1920, 'top': 0}
        x, y = apply_virtual_desktop_offset(500, 300, virtual_bounds)

        self.assert_equal(x, 2420.0, "x adjusted (500 - (-1920))")
        self.assert_equal(y, 300.0, "y adjusted (300 - 0)")

    def test_stage5_sendinput_normalization(self):
        """Test Stage 5: SendInput normalization"""
        print("\nTest: Stage 5 - SendInput Normalization")

        virtual_bounds = {
            'left': 0,
            'top': 0,
            'width': 1920,
            'height': 1080
        }

        # Test center of screen
        x_norm, y_norm = normalize_for_sendinput(960, 540, virtual_bounds)

        # Center should be approximately 32767 (half of 65535)
        expected_x = (960 * 65535) // 1920
        expected_y = (540 * 65535) // 1080

        self.assert_equal(x_norm, expected_x, f"x_norm (center)")
        self.assert_equal(y_norm, expected_y, f"y_norm (center)")

        # Test corner (0, 0)
        x_norm, y_norm = normalize_for_sendinput(0, 0, virtual_bounds)
        self.assert_equal(x_norm, 0, "x_norm (0, 0)")
        self.assert_equal(y_norm, 0, "y_norm (0, 0)")

        # Test opposite corner
        x_norm, y_norm = normalize_for_sendinput(1920, 1080, virtual_bounds)
        self.assert_equal(x_norm, 65535, "x_norm (max)")
        self.assert_equal(y_norm, 65535, "y_norm (max)")

    def test_stage6_calibration_homography(self):
        """Test Stage 6: Calibration with homography"""
        print("\nTest: Stage 6 - Calibration (Homography)")

        # Create synthetic calibration data with systematic offset
        src_points = np.array([
            [100, 100], [500, 100], [900, 100],
            [100, 500], [500, 500], [900, 500],
            [100, 900], [500, 900], [900, 900]
        ], dtype=float)

        # Add systematic offset (5 pixels in x, -3 pixels in y)
        dst_points = src_points + np.array([5, -3])

        # Mock DPI Manager
        with patch('coordinate_transformer.DPIManager') as MockDPI:
            mock_dpi = MockDPI.return_value
            mock_dpi.awareness_level = "Mocked"
            mock_dpi.get_virtual_screen_bounds.return_value = {
                'left': 0, 'top': 0, 'width': 1920, 'height': 1080
            }

            transformer = CoordinateTransformer(dpi_manager=mock_dpi, use_calibration=True)
            transformer.calibrate(dst_points, src_points, use_ransac=False)

            # Test correction on new point
            test_point = np.array([400, 400])
            test_measured = test_point + np.array([5, -3])

            corrected_x, corrected_y = transformer._apply_calibration(
                test_measured[0], test_measured[1]
            )

            # Should correct back to original
            self.assert_almost_equal(corrected_x, 400.0, tolerance=1.0,
                                    message="calibrated x")
            self.assert_almost_equal(corrected_y, 400.0, tolerance=1.0,
                                    message="calibrated y")

    def test_complete_pipeline(self):
        """Test complete 7-stage pipeline"""
        print("\nTest: Complete 7-Stage Pipeline")

        # Mock DPI Manager
        with patch('coordinate_transformer.DPIManager') as MockDPI:
            mock_dpi = MockDPI.return_value
            mock_dpi.awareness_level = "Mocked"
            mock_dpi.get_virtual_screen_bounds.return_value = {
                'left': 0, 'top': 0, 'width': 1920, 'height': 1080
            }

            transformer = CoordinateTransformer(dpi_manager=mock_dpi, use_calibration=False)

            # Test XYXY bbox
            bbox = [100, 200, 300, 400]
            result = transformer.transform(bbox, OCRFormat.XYXY)

            # Verify all stages recorded
            self.assert_equal('stage1_normalized' in result.stages, True,
                            "stage1 recorded")
            self.assert_equal('stage2_center' in result.stages, True,
                            "stage2 recorded")
            self.assert_equal('stage5_normalized' in result.stages, True,
                            "stage5 recorded")
            self.assert_equal('stage6_calibrated' in result.stages, True,
                            "stage6 recorded")

            # Verify center calculation
            expected_center = (200, 300)
            self.assert_equal(result.stages['stage2_center'], expected_center,
                            "center calculation")

            # Verify final coordinates
            self.assert_equal(result.final_x, 200, "final x")
            self.assert_equal(result.final_y, 300, "final y")

            # Verify validation passed
            self.assert_equal(result.validation_passed, True, "validation passed")

    def test_screenshot_scaling(self):
        """Test Stage 3: Screenshot to screen scaling"""
        print("\nTest: Stage 3 - Screenshot Scaling")

        with patch('coordinate_transformer.DPIManager') as MockDPI:
            mock_dpi = MockDPI.return_value
            mock_dpi.awareness_level = "Mocked"
            mock_dpi.get_virtual_screen_bounds.return_value = {
                'left': 0, 'top': 0, 'width': 1920, 'height': 1080
            }

            transformer = CoordinateTransformer(dpi_manager=mock_dpi)

            # Screenshot at 1280x720, screen at 1920x1080
            bbox = [100, 100, 200, 200]  # Center at (150, 150) in screenshot
            result = transformer.transform(
                bbox, OCRFormat.XYXY,
                screenshot_size=(1280, 720),
                screen_size=(1920, 1080)
            )

            # Expected scaling: 1920/1280 = 1.5x, 1080/720 = 1.5x
            # Center (150, 150) -> (225, 225)
            expected_x = 225
            expected_y = 225

            self.assert_equal(result.final_x, expected_x, "scaled x")
            self.assert_equal(result.final_y, expected_y, "scaled y")

    def test_bounding_box_properties(self):
        """Test BoundingBox helper properties"""
        print("\nTest: BoundingBox Properties")

        bbox = BoundingBox(100, 200, 300, 400)

        self.assert_equal(bbox.width, 200.0, "width")
        self.assert_equal(bbox.height, 200.0, "height")
        self.assert_equal(bbox.center, (200.0, 300.0), "center")
        self.assert_equal(bbox.to_tuple(), (100, 200, 300, 400), "to_tuple")

    def test_validation(self):
        """Test Stage 7: Validation"""
        print("\nTest: Stage 7 - Validation")

        with patch('coordinate_transformer.DPIManager') as MockDPI:
            mock_dpi = MockDPI.return_value
            mock_dpi.awareness_level = "Mocked"
            mock_dpi.get_virtual_screen_bounds.return_value = {
                'left': 0, 'top': 0, 'width': 1920, 'height': 1080
            }

            transformer = CoordinateTransformer(dpi_manager=mock_dpi)

            # Test valid coordinates
            is_valid, error = transformer._validate_coordinates(
                500, 500, 16384, 16384, screen_size=(1920, 1080)
            )
            self.assert_equal(is_valid, True, "valid coordinates")
            self.assert_equal(error, None, "no error message")

            # Test invalid SendInput coordinates
            is_valid, error = transformer._validate_coordinates(
                500, 500, 70000, 16384
            )
            self.assert_equal(is_valid, False, "invalid x_norm")
            self.assert_equal(error is not None, True, "error message present")

    def test_ransac_calibration(self):
        """Test RANSAC calibration with outliers"""
        print("\nTest: RANSAC Calibration with Outliers")

        # Create calibration data with outliers
        np.random.seed(42)
        n_points = 50
        src_points = np.random.uniform([100, 100], [900, 900], (n_points, 2))

        # Add systematic offset
        dst_points = src_points + np.array([5, -3])

        # Add outliers (10% of points)
        n_outliers = 5
        outlier_indices = np.random.choice(n_points, n_outliers, replace=False)
        dst_points[outlier_indices] += np.random.uniform(-50, 50, (n_outliers, 2))

        with patch('coordinate_transformer.DPIManager') as MockDPI:
            mock_dpi = MockDPI.return_value
            mock_dpi.awareness_level = "Mocked"
            mock_dpi.get_virtual_screen_bounds.return_value = {
                'left': 0, 'top': 0, 'width': 1920, 'height': 1080
            }

            transformer = CoordinateTransformer(dpi_manager=mock_dpi, use_calibration=True)

            # Calibrate with RANSAC (should reject outliers)
            transformer.calibrate(dst_points, src_points, use_ransac=True,
                                ransac_threshold=10.0)

            # Verify calibration succeeded
            self.assert_equal(transformer.is_calibrated, True, "calibration completed")

            # Test on inlier point
            test_point = np.array([500, 500])
            test_measured = test_point + np.array([5, -3])

            corrected_x, corrected_y = transformer._apply_calibration(
                test_measured[0], test_measured[1]
            )

            # Should correct reasonably well (within 5px)
            error = np.sqrt((corrected_x - 500)**2 + (corrected_y - 500)**2)
            self.assert_almost_equal(error, 0.0, tolerance=5.0,
                                    message="RANSAC correction error")

    def run_all_tests(self):
        """Run all tests"""
        print("="*70)
        print("COORDINATE TRANSFORMER TEST SUITE")
        print("="*70)

        # Run all test methods
        test_methods = [
            self.test_stage1_normalize_bbox_xyxy,
            self.test_stage1_normalize_bbox_xywh,
            self.test_stage1_normalize_bbox_quad,
            self.test_stage1_normalize_bbox_normalized,
            self.test_stage2_center_calculation,
            self.test_stage4_virtual_desktop_offset,
            self.test_stage5_sendinput_normalization,
            self.test_stage6_calibration_homography,
            self.test_complete_pipeline,
            self.test_screenshot_scaling,
            self.test_bounding_box_properties,
            self.test_validation,
            self.test_ransac_calibration,
        ]

        for test in test_methods:
            try:
                test()
            except Exception as e:
                print(f"\n  ✗ EXCEPTION in {test.__name__}: {e}")
                import traceback
                traceback.print_exc()
                self.failed += 1

        # Print summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {self.passed} ({pass_rate:.1f}%)")
        print(f"Failed: {self.failed}")

        if self.failed == 0:
            print("\n✓ ALL TESTS PASSED")
        else:
            print(f"\n✗ {self.failed} TEST(S) FAILED")

        return self.failed == 0


if __name__ == "__main__":
    test_suite = TestCoordinateTransformer()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)
