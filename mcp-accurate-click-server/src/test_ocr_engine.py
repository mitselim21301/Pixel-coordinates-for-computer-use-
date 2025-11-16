"""
Comprehensive Test Suite for OCR Engine
Tests all functionality including multi-pass averaging, screen capture, and text finding.
"""

import sys
import logging
import numpy as np
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ocr_engine import (
    OCREngine,
    ScreenCapture,
    BoundingBox,
    MonitorInfo,
    detect_gpu_support,
    benchmark_ocr_speed
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestOCREngine:
    """Test suite for OCR Engine"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.ocr = None
        self.capture = None

    def setup(self):
        """Initialize test environment"""
        logger.info("="*70)
        logger.info("OCR ENGINE TEST SUITE")
        logger.info("="*70)

        # Detect GPU
        gpu_available = detect_gpu_support()
        logger.info(f"GPU Support: {'Available' if gpu_available else 'Not Available'}")

        # Initialize components
        try:
            self.ocr = OCREngine(
                use_gpu=gpu_available,
                num_passes=3,
                min_confidence=0.5,
                show_log=False
            )
            logger.info("✓ OCR Engine initialized")
            self.passed += 1
        except Exception as e:
            logger.error(f"✗ Failed to initialize OCR Engine: {e}")
            self.failed += 1
            return False

        try:
            self.capture = ScreenCapture()
            logger.info("✓ Screen Capture initialized")
            self.passed += 1
        except Exception as e:
            logger.error(f"✗ Failed to initialize Screen Capture: {e}")
            self.failed += 1
            return False

        return True

    def test_monitor_detection(self):
        """Test multi-monitor detection"""
        logger.info("\n--- Test: Monitor Detection ---")

        try:
            monitors = self.capture.get_all_monitors()
            logger.info(f"Detected {len(monitors)} monitors")

            for monitor in monitors:
                logger.info(
                    f"  Monitor {monitor.index}: {monitor.width}x{monitor.height} "
                    f"at ({monitor.left}, {monitor.top})"
                )
                assert monitor.width > 0, "Monitor width must be positive"
                assert monitor.height > 0, "Monitor height must be positive"

            # Test monitor info retrieval
            for i in range(len(monitors)):
                info = self.capture.get_monitor_info(i)
                assert isinstance(info, MonitorInfo)
                assert info.index == i

            logger.info("✓ Monitor detection test passed")
            self.passed += 1

        except Exception as e:
            logger.error(f"✗ Monitor detection test failed: {e}")
            self.failed += 1

    def test_screen_capture(self):
        """Test screen capture functionality"""
        logger.info("\n--- Test: Screen Capture ---")

        try:
            # Capture primary monitor
            img, path = self.capture.capture_screen(monitor_number=1)

            logger.info(f"Screenshot saved to: {path}")
            logger.info(f"Image shape: {img.shape}")
            logger.info(f"Image dtype: {img.dtype}")

            # Verify image properties
            assert img.ndim == 3, "Image should be 3D array (H, W, C)"
            assert img.shape[2] == 3, "Image should have 3 channels (RGB)"
            assert Path(path).exists(), "Screenshot file should exist"
            assert Path(path).stat().st_size > 0, "Screenshot file should not be empty"

            logger.info("✓ Screen capture test passed")
            self.passed += 1

            return path  # Return path for next tests

        except Exception as e:
            logger.error(f"✗ Screen capture test failed: {e}")
            self.failed += 1
            return None

    def test_bounding_box(self):
        """Test BoundingBox class"""
        logger.info("\n--- Test: BoundingBox Class ---")

        try:
            # Create test bounding box
            bbox = BoundingBox(
                x_min=100.0,
                y_min=200.0,
                x_max=300.0,
                y_max=250.0,
                text="Test Text",
                confidence=0.95,
                quad=[[100, 200], [300, 200], [300, 250], [100, 250]],
                angle=0.0
            )

            # Test properties
            assert bbox.width == 200.0, "Width calculation incorrect"
            assert bbox.height == 50.0, "Height calculation incorrect"
            assert bbox.area == 10000.0, "Area calculation incorrect"
            assert bbox.center == (200.0, 225.0), "Center calculation incorrect"

            # Test serialization
            bbox_dict = bbox.to_dict()
            assert isinstance(bbox_dict, dict)
            assert bbox_dict['text'] == "Test Text"
            assert bbox_dict['confidence'] == 0.95

            logger.info("✓ BoundingBox class test passed")
            self.passed += 1

        except Exception as e:
            logger.error(f"✗ BoundingBox class test failed: {e}")
            self.failed += 1

    def test_ocr_extraction(self, screenshot_path: str):
        """Test OCR text extraction"""
        logger.info("\n--- Test: OCR Text Extraction ---")

        if not screenshot_path:
            logger.warning("Skipping OCR extraction test (no screenshot)")
            return

        try:
            # Test single-pass extraction
            logger.info("Testing single-pass OCR...")
            bboxes_single = self.ocr.extract_text_coordinates(
                screenshot_path,
                use_averaging=False,
                confidence_threshold=0.3
            )
            logger.info(f"Single-pass detected {len(bboxes_single)} text regions")

            # Test multi-pass extraction
            logger.info("Testing multi-pass OCR with averaging...")
            bboxes_multi = self.ocr.extract_text_coordinates(
                screenshot_path,
                use_averaging=True,
                confidence_threshold=0.3
            )
            logger.info(f"Multi-pass detected {len(bboxes_multi)} text regions")

            # Verify results
            for bbox in bboxes_multi[:5]:  # Show first 5
                logger.info(
                    f"  '{bbox.text}' at {bbox.quad_center} "
                    f"(conf: {bbox.confidence:.2%}, angle: {bbox.angle:.1f}°)"
                )

                # Validate bbox properties
                assert bbox.x_min >= 0, "x_min should be non-negative"
                assert bbox.y_min >= 0, "y_min should be non-negative"
                assert bbox.x_max > bbox.x_min, "x_max should be greater than x_min"
                assert bbox.y_max > bbox.y_min, "y_max should be greater than y_min"
                assert 0 <= bbox.confidence <= 1, "Confidence should be in [0, 1]"

            logger.info("✓ OCR extraction test passed")
            self.passed += 1

            return bboxes_multi

        except Exception as e:
            logger.error(f"✗ OCR extraction test failed: {e}")
            self.failed += 1
            return None

    def test_text_finding(self, screenshot_path: str, bboxes: List[BoundingBox]):
        """Test find_text functionality"""
        logger.info("\n--- Test: Text Finding ---")

        if not screenshot_path or not bboxes:
            logger.warning("Skipping text finding test (no data)")
            return

        try:
            # Test finding existing text
            if bboxes:
                target_text = bboxes[0].text
                logger.info(f"Searching for: '{target_text}'")

                result = self.ocr.find_text(
                    screenshot_path,
                    target_text,
                    fuzzy_threshold=0.7,
                    use_averaging=True
                )

                if result:
                    logger.info(f"✓ Found '{result.text}' at {result.quad_center}")
                    logger.info(f"  Confidence: {result.confidence:.2%}")
                    assert result.text.lower() == target_text.lower() or \
                           self.ocr._text_similarity(result.text.lower(), target_text.lower()) >= 0.7
                else:
                    logger.warning(f"Text '{target_text}' not found (may be normal)")

            # Test finding non-existent text
            result = self.ocr.find_text(
                screenshot_path,
                "ThisTextDefinitelyDoesNotExist12345",
                fuzzy_threshold=0.9,
                use_averaging=False
            )

            assert result is None, "Should not find non-existent text"

            logger.info("✓ Text finding test passed")
            self.passed += 1

        except Exception as e:
            logger.error(f"✗ Text finding test failed: {e}")
            self.failed += 1

    def test_caching(self, screenshot_path: str):
        """Test result caching"""
        logger.info("\n--- Test: Result Caching ---")

        if not screenshot_path:
            logger.warning("Skipping caching test (no screenshot)")
            return

        try:
            # Enable caching
            self.ocr.set_cache_enabled(True)
            self.ocr.clear_cache()

            # First call (should cache)
            import time
            start = time.time()
            result1 = self.ocr.extract_text_coordinates(screenshot_path, use_averaging=False)
            time1 = time.time() - start

            # Second call (should use cache)
            start = time.time()
            result2 = self.ocr.extract_text_coordinates(screenshot_path, use_averaging=False)
            time2 = time.time() - start

            logger.info(f"First call: {time1:.3f}s")
            logger.info(f"Second call (cached): {time2:.3f}s")
            logger.info(f"Speedup: {time1/time2:.1f}x")

            # Verify results are identical
            assert len(result1) == len(result2), "Cached results should match"

            # Clear cache
            self.ocr.clear_cache()

            logger.info("✓ Caching test passed")
            self.passed += 1

        except Exception as e:
            logger.error(f"✗ Caching test failed: {e}")
            self.failed += 1

    def test_error_handling(self):
        """Test error handling"""
        logger.info("\n--- Test: Error Handling ---")

        try:
            # Test invalid image path
            try:
                self.ocr.extract_text_coordinates("/nonexistent/path.png")
                assert False, "Should raise FileNotFoundError"
            except FileNotFoundError:
                logger.info("✓ Correctly raised FileNotFoundError for invalid path")

            # Test invalid monitor number
            try:
                self.capture.capture_screen(monitor_number=999)
                assert False, "Should raise ValueError"
            except ValueError:
                logger.info("✓ Correctly raised ValueError for invalid monitor")

            # Test invalid region
            try:
                self.capture.capture_region(0, 0, -100, -100)
                assert False, "Should raise ValueError"
            except ValueError:
                logger.info("✓ Correctly raised ValueError for invalid region")

            logger.info("✓ Error handling test passed")
            self.passed += 1

        except Exception as e:
            logger.error(f"✗ Error handling test failed: {e}")
            self.failed += 1

    def test_coordinate_conversion(self):
        """Test coordinate conversion methods"""
        logger.info("\n--- Test: Coordinate Conversion ---")

        try:
            # Test quad to XYXY conversion
            quad = [[100, 200], [300, 220], [290, 250], [95, 245]]
            bbox = self.ocr._convert_quad_to_xyxy(quad, "Test", 0.9)

            assert bbox.x_min == 95.0, "x_min should be min of all x coordinates"
            assert bbox.y_min == 200.0, "y_min should be min of all y coordinates"
            assert bbox.x_max == 300.0, "x_max should be max of all x coordinates"
            assert bbox.y_max == 250.0, "y_max should be max of all y coordinates"

            # Test rotation angle computation
            horizontal_quad = [[100, 200], [300, 200], [300, 250], [100, 250]]
            angle = self.ocr._compute_rotation_angle(horizontal_quad)
            assert abs(angle) < 1.0, "Horizontal text should have ~0° angle"

            logger.info("✓ Coordinate conversion test passed")
            self.passed += 1

        except Exception as e:
            logger.error(f"✗ Coordinate conversion test failed: {e}")
            self.failed += 1

    def test_similarity_functions(self):
        """Test text and position similarity functions"""
        logger.info("\n--- Test: Similarity Functions ---")

        try:
            # Test text similarity
            sim1 = self.ocr._text_similarity("hello", "hello")
            assert sim1 == 1.0, "Identical strings should have similarity 1.0"

            sim2 = self.ocr._text_similarity("hello", "hallo")
            assert 0.5 < sim2 < 1.0, "Similar strings should have high similarity"

            sim3 = self.ocr._text_similarity("hello", "world")
            assert sim3 < 0.5, "Different strings should have low similarity"

            # Test position similarity (IoU)
            bbox1 = BoundingBox(0, 0, 100, 100, "text1", 0.9)
            bbox2 = BoundingBox(0, 0, 100, 100, "text2", 0.9)
            iou1 = self.ocr._position_similarity(bbox1, bbox2)
            assert iou1 == 1.0, "Identical boxes should have IoU 1.0"

            bbox3 = BoundingBox(50, 50, 150, 150, "text3", 0.9)
            iou2 = self.ocr._position_similarity(bbox1, bbox3)
            assert 0 < iou2 < 1.0, "Overlapping boxes should have 0 < IoU < 1"

            bbox4 = BoundingBox(200, 200, 300, 300, "text4", 0.9)
            iou3 = self.ocr._position_similarity(bbox1, bbox4)
            assert iou3 == 0.0, "Non-overlapping boxes should have IoU 0.0"

            logger.info("✓ Similarity functions test passed")
            self.passed += 1

        except Exception as e:
            logger.error(f"✗ Similarity functions test failed: {e}")
            self.failed += 1

    def cleanup(self):
        """Cleanup test resources"""
        logger.info("\n--- Cleanup ---")

        try:
            if self.capture:
                self.capture.cleanup_temp_files()
                logger.info("✓ Temporary files cleaned up")

            if self.ocr:
                self.ocr.clear_cache()
                logger.info("✓ OCR cache cleared")

        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")

    def run_all_tests(self):
        """Run all tests"""
        if not self.setup():
            logger.error("Setup failed, aborting tests")
            return

        # Run tests
        self.test_monitor_detection()
        self.test_bounding_box()
        self.test_coordinate_conversion()
        self.test_similarity_functions()
        self.test_error_handling()

        # Tests requiring screenshot
        screenshot_path = self.test_screen_capture()
        if screenshot_path:
            bboxes = self.test_ocr_extraction(screenshot_path)
            self.test_text_finding(screenshot_path, bboxes)
            self.test_caching(screenshot_path)

        # Cleanup
        self.cleanup()

        # Print summary
        logger.info("\n" + "="*70)
        logger.info("TEST SUMMARY")
        logger.info("="*70)
        logger.info(f"Tests Passed: {self.passed}")
        logger.info(f"Tests Failed: {self.failed}")
        logger.info(f"Total Tests:  {self.passed + self.failed}")

        if self.failed == 0:
            logger.info("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        else:
            logger.warning(f"\n⚠ {self.failed} TEST(S) FAILED")

        logger.info("="*70)

        return self.failed == 0


def main():
    """Main test entry point"""
    tester = TestOCREngine()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
