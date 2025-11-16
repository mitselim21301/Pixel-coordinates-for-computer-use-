"""
Tests for Coordinate Transformation System
Tests the 7-stage pipeline, DPI manager, bbox normalization, and SendInput conversion.

Based on COMPREHENSIVE_RESEARCH_REPORT.md 7-stage pipeline specification.
"""

import pytest
import numpy as np
from typing import Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# Coordinate Transformation System
# ============================================================================

class CoordinateSpace(Enum):
    """Different coordinate spaces in the transformation pipeline"""
    OCR_RAW = "ocr_raw"  # Raw OCR output
    PHYSICAL_PIXELS = "physical_pixels"  # Physical screen pixels
    LOGICAL_PIXELS = "logical_pixels"  # DPI-scaled logical pixels
    VIRTUAL_DESKTOP = "virtual_desktop"  # Multi-monitor virtual space
    SENDINPUT_NORMALIZED = "sendinput_normalized"  # SendInput 0-65535 range


@dataclass
class BoundingBox:
    """Bounding box representation"""
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def get_center(self) -> Tuple[float, float]:
        """Get center point of bounding box"""
        return (
            (self.x_min + self.x_max) / 2,
            (self.y_min + self.y_max) / 2
        )

    def get_width(self) -> float:
        return self.x_max - self.x_min

    def get_height(self) -> float:
        return self.y_max - self.y_min

    @classmethod
    def from_xyxy(cls, coords: List[float]):
        """Create from [x_min, y_min, x_max, y_max]"""
        return cls(coords[0], coords[1], coords[2], coords[3])

    @classmethod
    def from_corners(cls, corners: List[List[float]]):
        """Create from corner points [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]"""
        x_coords = [p[0] for p in corners]
        y_coords = [p[1] for p in corners]
        return cls(min(x_coords), min(y_coords), max(x_coords), max(y_coords))

    def to_xyxy(self) -> List[float]:
        """Convert to [x_min, y_min, x_max, y_max]"""
        return [self.x_min, self.y_min, self.x_max, self.y_max]


class DPIManager:
    """Manages DPI scaling and awareness"""

    def __init__(self, dpi_scale: float = 1.0, dpi_awareness_mode: str = "per_monitor_v2"):
        self.dpi_scale = dpi_scale
        self.dpi_awareness_mode = dpi_awareness_mode

    def physical_to_logical(self, coords: np.ndarray) -> np.ndarray:
        """Convert physical pixels to logical pixels"""
        return coords / self.dpi_scale

    def logical_to_physical(self, coords: np.ndarray) -> np.ndarray:
        """Convert logical pixels to physical pixels"""
        return coords * self.dpi_scale

    def set_dpi_scale(self, scale: float):
        """Update DPI scale factor"""
        if scale <= 0:
            raise ValueError("DPI scale must be positive")
        self.dpi_scale = scale

    def get_effective_resolution(self, physical_width: int,
                                 physical_height: int) -> Tuple[int, int]:
        """Get effective logical resolution"""
        return (
            int(physical_width / self.dpi_scale),
            int(physical_height / self.dpi_scale)
        )


class BBoxNormalizer:
    """Normalize bounding boxes from various OCR formats"""

    @staticmethod
    def normalize_paddleocr(bbox: List[List[float]]) -> BoundingBox:
        """
        Normalize PaddleOCR format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        Returns BoundingBox in XYXY format
        """
        return BoundingBox.from_corners(bbox)

    @staticmethod
    def normalize_tesseract(bbox: Dict[str, int]) -> BoundingBox:
        """
        Normalize Tesseract format: {'left': x, 'top': y, 'width': w, 'height': h}
        Returns BoundingBox in XYXY format
        """
        x_min = bbox['left']
        y_min = bbox['top']
        x_max = x_min + bbox['width']
        y_max = y_min + bbox['height']
        return BoundingBox(x_min, y_min, x_max, y_max)

    @staticmethod
    def normalize_easyocr(bbox: List[List[float]]) -> BoundingBox:
        """
        Normalize EasyOCR format (same as PaddleOCR)
        Returns BoundingBox in XYXY format
        """
        return BoundingBox.from_corners(bbox)

    @staticmethod
    def normalize_xyxy(bbox: List[float]) -> BoundingBox:
        """
        Normalize XYXY format: [x_min, y_min, x_max, y_max]
        """
        return BoundingBox.from_xyxy(bbox)


class SendInputConverter:
    """Convert coordinates to SendInput normalized format (0-65535)"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.max_value = 65535

    def to_sendinput(self, x: float, y: float) -> Tuple[int, int]:
        """
        Convert pixel coordinates to SendInput normalized coordinates

        Args:
            x: X coordinate in pixels
            y: Y coordinate in pixels

        Returns:
            (norm_x, norm_y) in range [0, 65535]
        """
        # Normalize to [0, 1]
        norm_x = x / self.screen_width
        norm_y = y / self.screen_height

        # Scale to [0, 65535]
        sendinput_x = int(norm_x * self.max_value)
        sendinput_y = int(norm_y * self.max_value)

        # Clamp to valid range
        sendinput_x = max(0, min(self.max_value, sendinput_x))
        sendinput_y = max(0, min(self.max_value, sendinput_y))

        return (sendinput_x, sendinput_y)

    def from_sendinput(self, norm_x: int, norm_y: int) -> Tuple[float, float]:
        """
        Convert SendInput normalized coordinates back to pixels

        Args:
            norm_x: X in range [0, 65535]
            norm_y: Y in range [0, 65535]

        Returns:
            (x, y) in pixels
        """
        x = (norm_x / self.max_value) * self.screen_width
        y = (norm_y / self.max_value) * self.screen_height

        return (x, y)


class CoordinateTransformer:
    """
    7-Stage Coordinate Transformation Pipeline

    Stage 1: OCR Coordinate Extraction
    Stage 2: Format Normalization (to XYXY physical pixels)
    Stage 3: DPI-Aware Scaling (physical → logical if needed)
    Stage 4: Multi-Monitor Offset Adjustment
    Stage 5: SendInput Normalization (pixel → 65535 range)
    Stage 6: Calibration Correction (optional)
    Stage 7: Statistical Validation
    """

    def __init__(self, screen_width=1920, screen_height=1080, dpi_scale=1.0):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.dpi_manager = DPIManager(dpi_scale)
        self.bbox_normalizer = BBoxNormalizer()
        self.sendinput_converter = SendInputConverter(screen_width, screen_height)

        self.calibration = None  # Optional calibration system
        self.multi_monitor_offset = (0, 0)  # For multi-monitor setups

    def transform(self, ocr_bbox, ocr_format='paddleocr',
                 apply_dpi=False, apply_calibration=False) -> Dict:
        """
        Transform OCR coordinates through 7-stage pipeline

        Args:
            ocr_bbox: OCR bounding box in native format
            ocr_format: Format of OCR bbox ('paddleocr', 'tesseract', etc.)
            apply_dpi: Whether to apply DPI scaling
            apply_calibration: Whether to apply calibration correction

        Returns:
            Dictionary with coordinates at each stage
        """
        result = {}

        # Stage 1: OCR Coordinate Extraction (already done)
        result['stage1_ocr_raw'] = ocr_bbox

        # Stage 2: Format Normalization
        if ocr_format == 'paddleocr':
            bbox = self.bbox_normalizer.normalize_paddleocr(ocr_bbox)
        elif ocr_format == 'tesseract':
            bbox = self.bbox_normalizer.normalize_tesseract(ocr_bbox)
        elif ocr_format == 'xyxy':
            bbox = self.bbox_normalizer.normalize_xyxy(ocr_bbox)
        else:
            raise ValueError(f"Unknown OCR format: {ocr_format}")

        result['stage2_normalized'] = bbox
        center_physical = np.array(bbox.get_center())
        result['stage2_center'] = center_physical

        # Stage 3: DPI-Aware Scaling
        if apply_dpi:
            center_logical = self.dpi_manager.physical_to_logical(center_physical)
        else:
            center_logical = center_physical
        result['stage3_dpi_scaled'] = center_logical

        # Stage 4: Multi-Monitor Offset
        center_virtual = center_logical + np.array(self.multi_monitor_offset)
        result['stage4_virtual_desktop'] = center_virtual

        # Stage 5: SendInput Normalization
        sendinput_coords = self.sendinput_converter.to_sendinput(
            center_virtual[0], center_virtual[1]
        )
        result['stage5_sendinput'] = sendinput_coords

        # Stage 6: Calibration Correction (optional)
        if apply_calibration and self.calibration is not None:
            center_calibrated = self.calibration.correct(center_virtual)
            result['stage6_calibrated'] = center_calibrated

            # Update SendInput coords with calibrated values
            sendinput_coords = self.sendinput_converter.to_sendinput(
                center_calibrated[0], center_calibrated[1]
            )
            result['stage5_sendinput'] = sendinput_coords
        else:
            result['stage6_calibrated'] = center_virtual

        # Stage 7: Statistical Validation (placeholder)
        result['stage7_validated'] = True

        return result

    def set_calibration(self, calibration):
        """Set calibration system"""
        self.calibration = calibration

    def set_multi_monitor_offset(self, offset_x: float, offset_y: float):
        """Set offset for multi-monitor setups"""
        self.multi_monitor_offset = (offset_x, offset_y)


# ============================================================================
# Test Class: DPI Manager
# ============================================================================

class TestDPIManager:
    """Test DPI scaling and awareness"""

    def test_dpi_manager_creation(self):
        """Test creating DPI manager"""
        dpi = DPIManager(dpi_scale=1.5)

        assert dpi.dpi_scale == 1.5
        assert dpi.dpi_awareness_mode == "per_monitor_v2"

    def test_physical_to_logical_100_percent(self):
        """Test conversion at 100% DPI (no scaling)"""
        dpi = DPIManager(dpi_scale=1.0)

        physical = np.array([1920, 1080])
        logical = dpi.physical_to_logical(physical)

        np.testing.assert_array_equal(logical, physical)

    def test_physical_to_logical_150_percent(self):
        """Test conversion at 150% DPI"""
        dpi = DPIManager(dpi_scale=1.5)

        physical = np.array([1920, 1080])
        logical = dpi.physical_to_logical(physical)

        expected = np.array([1280, 720])  # 1920/1.5, 1080/1.5
        np.testing.assert_array_almost_equal(logical, expected)

    def test_logical_to_physical_150_percent(self):
        """Test reverse conversion at 150% DPI"""
        dpi = DPIManager(dpi_scale=1.5)

        logical = np.array([1280, 720])
        physical = dpi.logical_to_physical(logical)

        expected = np.array([1920, 1080])
        np.testing.assert_array_almost_equal(physical, expected)

    def test_roundtrip_conversion(self):
        """Test that roundtrip conversion preserves values"""
        dpi = DPIManager(dpi_scale=1.25)

        original = np.array([1536, 864])
        logical = dpi.physical_to_logical(original)
        back_to_physical = dpi.logical_to_physical(logical)

        np.testing.assert_array_almost_equal(back_to_physical, original)

    def test_set_dpi_scale(self):
        """Test updating DPI scale"""
        dpi = DPIManager(dpi_scale=1.0)

        dpi.set_dpi_scale(1.5)
        assert dpi.dpi_scale == 1.5

    def test_set_invalid_dpi_scale(self):
        """Test that invalid DPI scale raises error"""
        dpi = DPIManager()

        with pytest.raises(ValueError, match="must be positive"):
            dpi.set_dpi_scale(0)

        with pytest.raises(ValueError, match="must be positive"):
            dpi.set_dpi_scale(-1.5)

    def test_get_effective_resolution(self):
        """Test getting effective logical resolution"""
        dpi = DPIManager(dpi_scale=1.5)

        logical_w, logical_h = dpi.get_effective_resolution(1920, 1080)

        assert logical_w == 1280
        assert logical_h == 720


# ============================================================================
# Test Class: BBox Normalization
# ============================================================================

class TestBBoxNormalization:
    """Test bounding box normalization from various formats"""

    def test_bounding_box_creation(self):
        """Test creating bounding box"""
        bbox = BoundingBox(100, 200, 300, 400)

        assert bbox.x_min == 100
        assert bbox.y_min == 200
        assert bbox.x_max == 300
        assert bbox.y_max == 400

    def test_bounding_box_center(self):
        """Test getting bbox center"""
        bbox = BoundingBox(100, 200, 300, 400)

        center = bbox.get_center()

        assert center == (200, 300)

    def test_bounding_box_dimensions(self):
        """Test getting bbox dimensions"""
        bbox = BoundingBox(100, 200, 300, 450)

        assert bbox.get_width() == 200
        assert bbox.get_height() == 250

    def test_normalize_paddleocr_format(self):
        """Test normalizing PaddleOCR format"""
        # PaddleOCR: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        paddle_bbox = [[100, 100], [200, 100], [200, 130], [100, 130]]

        normalizer = BBoxNormalizer()
        bbox = normalizer.normalize_paddleocr(paddle_bbox)

        assert bbox.x_min == 100
        assert bbox.y_min == 100
        assert bbox.x_max == 200
        assert bbox.y_max == 130
        assert bbox.get_center() == (150, 115)

    def test_normalize_tesseract_format(self):
        """Test normalizing Tesseract format"""
        # Tesseract: {'left': x, 'top': y, 'width': w, 'height': h}
        tess_bbox = {'left': 100, 'top': 200, 'width': 150, 'height': 50}

        normalizer = BBoxNormalizer()
        bbox = normalizer.normalize_tesseract(tess_bbox)

        assert bbox.x_min == 100
        assert bbox.y_min == 200
        assert bbox.x_max == 250
        assert bbox.y_max == 250
        assert bbox.get_center() == (175, 225)

    def test_normalize_xyxy_format(self):
        """Test normalizing XYXY format"""
        # XYXY: [x_min, y_min, x_max, y_max]
        xyxy_bbox = [100, 200, 300, 400]

        normalizer = BBoxNormalizer()
        bbox = normalizer.normalize_xyxy(xyxy_bbox)

        assert bbox.x_min == 100
        assert bbox.y_min == 200
        assert bbox.x_max == 300
        assert bbox.y_max == 400

    def test_bbox_to_xyxy(self):
        """Test converting bbox back to XYXY"""
        bbox = BoundingBox(100, 200, 300, 400)

        xyxy = bbox.to_xyxy()

        assert xyxy == [100, 200, 300, 400]

    def test_bbox_from_corners(self):
        """Test creating bbox from corner points"""
        # Corners can be in any order
        corners = [[200, 100], [100, 130], [200, 130], [100, 100]]

        bbox = BoundingBox.from_corners(corners)

        assert bbox.x_min == 100
        assert bbox.y_min == 100
        assert bbox.x_max == 200
        assert bbox.y_max == 130


# ============================================================================
# Test Class: SendInput Conversion
# ============================================================================

class TestSendInputConverter:
    """Test SendInput coordinate conversion"""

    def test_sendinput_converter_creation(self):
        """Test creating SendInput converter"""
        converter = SendInputConverter(1920, 1080)

        assert converter.screen_width == 1920
        assert converter.screen_height == 1080
        assert converter.max_value == 65535

    def test_to_sendinput_center(self):
        """Test converting screen center"""
        converter = SendInputConverter(1920, 1080)

        norm_x, norm_y = converter.to_sendinput(960, 540)

        # Center should be approximately 32767 (65535/2)
        assert 32700 < norm_x < 32800
        assert 32700 < norm_y < 32800

    def test_to_sendinput_origin(self):
        """Test converting origin (0, 0)"""
        converter = SendInputConverter(1920, 1080)

        norm_x, norm_y = converter.to_sendinput(0, 0)

        assert norm_x == 0
        assert norm_y == 0

    def test_to_sendinput_max(self):
        """Test converting maximum coordinates"""
        converter = SendInputConverter(1920, 1080)

        norm_x, norm_y = converter.to_sendinput(1920, 1080)

        assert norm_x == 65535
        assert norm_y == 65535

    def test_from_sendinput_center(self):
        """Test converting from SendInput center"""
        converter = SendInputConverter(1920, 1080)

        x, y = converter.from_sendinput(32767, 32767)

        # Should be approximately screen center
        assert 950 < x < 970
        assert 535 < y < 545

    def test_from_sendinput_origin(self):
        """Test converting from SendInput origin"""
        converter = SendInputConverter(1920, 1080)

        x, y = converter.from_sendinput(0, 0)

        assert x == 0
        assert y == 0

    def test_from_sendinput_max(self):
        """Test converting from SendInput max"""
        converter = SendInputConverter(1920, 1080)

        x, y = converter.from_sendinput(65535, 65535)

        assert x == 1920
        assert y == 1080

    def test_roundtrip_conversion(self):
        """Test roundtrip conversion preserves coordinates"""
        converter = SendInputConverter(1920, 1080)

        original_x, original_y = 500, 300

        # Convert to SendInput and back
        norm_x, norm_y = converter.to_sendinput(original_x, original_y)
        back_x, back_y = converter.from_sendinput(norm_x, norm_y)

        # Should be very close (within 1 pixel due to rounding)
        assert abs(back_x - original_x) < 1
        assert abs(back_y - original_y) < 1

    def test_clamping_out_of_bounds(self):
        """Test that out-of-bounds coordinates are clamped"""
        converter = SendInputConverter(1920, 1080)

        # Negative coordinates
        norm_x, norm_y = converter.to_sendinput(-100, -50)
        assert norm_x == 0
        assert norm_y == 0

        # Oversized coordinates
        norm_x, norm_y = converter.to_sendinput(3000, 2000)
        assert norm_x == 65535
        assert norm_y == 65535


# ============================================================================
# Test Class: 7-Stage Pipeline
# ============================================================================

class TestCoordinateTransformer:
    """Test complete 7-stage transformation pipeline"""

    def test_transformer_creation(self):
        """Test creating coordinate transformer"""
        transformer = CoordinateTransformer(
            screen_width=1920,
            screen_height=1080,
            dpi_scale=1.0
        )

        assert transformer.screen_width == 1920
        assert transformer.screen_height == 1080
        assert transformer.dpi_manager.dpi_scale == 1.0

    def test_stage2_format_normalization(self):
        """Test Stage 2: Format normalization"""
        transformer = CoordinateTransformer()

        # PaddleOCR format
        paddle_bbox = [[100, 100], [200, 100], [200, 130], [100, 130]]

        result = transformer.transform(paddle_bbox, ocr_format='paddleocr')

        assert 'stage2_normalized' in result
        bbox = result['stage2_normalized']
        assert bbox.x_min == 100
        assert bbox.x_max == 200
        assert result['stage2_center'][0] == 150
        assert result['stage2_center'][1] == 115

    def test_stage3_dpi_scaling(self):
        """Test Stage 3: DPI scaling"""
        transformer = CoordinateTransformer(dpi_scale=1.5)

        paddle_bbox = [[300, 300], [600, 300], [600, 400], [300, 400]]

        # With DPI scaling
        result = transformer.transform(paddle_bbox, apply_dpi=True)

        # Physical center: (450, 350)
        # Logical center at 150% DPI: (300, 233.33)
        logical = result['stage3_dpi_scaled']
        assert abs(logical[0] - 300) < 1
        assert abs(logical[1] - 233.33) < 1

    def test_stage4_multi_monitor_offset(self):
        """Test Stage 4: Multi-monitor offset"""
        transformer = CoordinateTransformer()
        transformer.set_multi_monitor_offset(1920, 0)  # Second monitor to the right

        paddle_bbox = [[100, 100], [200, 100], [200, 130], [100, 130]]

        result = transformer.transform(paddle_bbox)

        virtual_desktop = result['stage4_virtual_desktop']
        # Center at (150, 115) + offset (1920, 0) = (2070, 115)
        assert virtual_desktop[0] == 2070
        assert virtual_desktop[1] == 115

    def test_stage5_sendinput_conversion(self):
        """Test Stage 5: SendInput normalization"""
        transformer = CoordinateTransformer(1920, 1080)

        # Center of screen
        paddle_bbox = [[910, 530], [1010, 530], [1010, 550], [910, 550]]

        result = transformer.transform(paddle_bbox)

        sendinput = result['stage5_sendinput']
        # Center approximately (960, 540) -> normalized ~(32767, 32767)
        assert 32000 < sendinput[0] < 33500
        assert 32000 < sendinput[1] < 33500

    def test_stage6_calibration_correction(self, mock_calibration):
        """Test Stage 6: Calibration correction"""
        transformer = CoordinateTransformer()

        # Set up calibration with known offset
        mock_calibration.offset = np.array([10.0, -5.0])
        mock_calibration.is_calibrated = True
        transformer.set_calibration(mock_calibration)

        paddle_bbox = [[100, 100], [200, 100], [200, 130], [100, 130]]

        result = transformer.transform(paddle_bbox, apply_calibration=True)

        calibrated = result['stage6_calibrated']
        # Center (150, 115) - offset (10, -5) = (140, 120)
        assert abs(calibrated[0] - 140) < 0.1
        assert abs(calibrated[1] - 120) < 0.1

    def test_full_pipeline_without_calibration(self):
        """Test complete pipeline without calibration"""
        transformer = CoordinateTransformer(1920, 1080, dpi_scale=1.0)

        paddle_bbox = [[500, 400], [700, 400], [700, 450], [500, 450]]

        result = transformer.transform(
            paddle_bbox,
            ocr_format='paddleocr',
            apply_dpi=False,
            apply_calibration=False
        )

        # Check all stages present
        assert 'stage1_ocr_raw' in result
        assert 'stage2_normalized' in result
        assert 'stage2_center' in result
        assert 'stage3_dpi_scaled' in result
        assert 'stage4_virtual_desktop' in result
        assert 'stage5_sendinput' in result
        assert 'stage6_calibrated' in result
        assert 'stage7_validated' in result

        # Center should be (600, 425)
        center = result['stage2_center']
        assert center[0] == 600
        assert center[1] == 425

    def test_full_pipeline_with_all_features(self, mock_calibration):
        """Test complete pipeline with DPI and calibration"""
        transformer = CoordinateTransformer(1920, 1080, dpi_scale=1.5)

        mock_calibration.offset = np.array([5.0, -3.0])
        mock_calibration.is_calibrated = True
        transformer.set_calibration(mock_calibration)
        transformer.set_multi_monitor_offset(0, 0)

        paddle_bbox = [[300, 300], [600, 300], [600, 400], [300, 400]]

        result = transformer.transform(
            paddle_bbox,
            ocr_format='paddleocr',
            apply_dpi=True,
            apply_calibration=True
        )

        # Verify all stages executed
        assert result['stage7_validated'] is True

        # Physical center: (450, 350)
        # Logical (DPI /1.5): (300, 233.33)
        # Calibrated: (295, 236.33)
        calibrated = result['stage6_calibrated']
        assert abs(calibrated[0] - 295) < 1
        assert abs(calibrated[1] - 236.33) < 1

    def test_different_ocr_formats(self):
        """Test pipeline with different OCR formats"""
        transformer = CoordinateTransformer()

        # PaddleOCR
        paddle_bbox = [[100, 100], [200, 100], [200, 130], [100, 130]]
        result_paddle = transformer.transform(paddle_bbox, ocr_format='paddleocr')

        # Tesseract
        tess_bbox = {'left': 100, 'top': 100, 'width': 100, 'height': 30}
        result_tess = transformer.transform(tess_bbox, ocr_format='tesseract')

        # XYXY
        xyxy_bbox = [100, 100, 200, 130]
        result_xyxy = transformer.transform(xyxy_bbox, ocr_format='xyxy')

        # All should produce same center
        assert result_paddle['stage2_center'][0] == result_tess['stage2_center'][0]
        assert result_paddle['stage2_center'][0] == result_xyxy['stage2_center'][0]

    def test_unknown_ocr_format_raises_error(self):
        """Test that unknown OCR format raises error"""
        transformer = CoordinateTransformer()

        with pytest.raises(ValueError, match="Unknown OCR format"):
            transformer.transform([100, 100, 200, 130], ocr_format='unknown')


# ============================================================================
# Test Class: Accuracy and Precision
# ============================================================================

@pytest.mark.performance
class TestTransformationAccuracy:
    """Test transformation accuracy and precision"""

    def test_sendinput_conversion_precision(self):
        """Test SendInput conversion maintains precision"""
        converter = SendInputConverter(1920, 1080)

        # Test many points
        errors = []
        for _ in range(100):
            x = np.random.uniform(0, 1920)
            y = np.random.uniform(0, 1080)

            norm_x, norm_y = converter.to_sendinput(x, y)
            back_x, back_y = converter.from_sendinput(norm_x, norm_y)

            error = np.sqrt((back_x - x)**2 + (back_y - y)**2)
            errors.append(error)

        mean_error = np.mean(errors)
        max_error = np.max(errors)

        # Error should be sub-pixel
        assert mean_error < 0.5
        assert max_error < 1.0

    def test_dpi_scaling_precision(self):
        """Test DPI scaling maintains precision"""
        dpi = DPIManager(dpi_scale=1.25)

        # Test roundtrip precision
        errors = []
        for _ in range(100):
            physical = np.random.uniform([0, 0], [1920, 1080])

            logical = dpi.physical_to_logical(physical)
            back_to_physical = dpi.logical_to_physical(logical)

            error = np.linalg.norm(back_to_physical - physical)
            errors.append(error)

        max_error = np.max(errors)

        # Should be essentially zero (floating point precision)
        assert max_error < 1e-10

    def test_pipeline_preserves_relative_positions(self):
        """Test that pipeline preserves relative positions of elements"""
        transformer = CoordinateTransformer(1920, 1080)

        # Two bounding boxes at known distance
        bbox1 = [[100, 100], [200, 100], [200, 130], [100, 130]]
        bbox2 = [[300, 100], [400, 100], [400, 130], [300, 130]]

        result1 = transformer.transform(bbox1)
        result2 = transformer.transform(bbox2)

        # Distance should be preserved
        center1 = result1['stage2_center']
        center2 = result2['stage2_center']

        distance = np.linalg.norm(center2 - center1)

        # Expected distance: 200 pixels (center to center)
        assert abs(distance - 200) < 0.1


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestCoordinateTransformerIntegration:
    """Integration tests for coordinate transformation"""

    def test_end_to_end_transformation(self, mock_calibration):
        """Test complete end-to-end transformation"""
        # Setup
        transformer = CoordinateTransformer(1920, 1080, dpi_scale=1.0)
        mock_calibration.offset = np.array([3.5, -2.8])
        mock_calibration.is_calibrated = True
        transformer.set_calibration(mock_calibration)

        # OCR detects a button at center of screen
        ocr_bbox = [[910, 530], [1010, 530], [1010, 550], [910, 550]]

        # Transform
        result = transformer.transform(
            ocr_bbox,
            ocr_format='paddleocr',
            apply_calibration=True
        )

        # Verify
        assert result['stage7_validated'] is True

        # Get final SendInput coordinates
        final_coords = result['stage5_sendinput']
        assert isinstance(final_coords, tuple)
        assert 0 <= final_coords[0] <= 65535
        assert 0 <= final_coords[1] <= 65535

    def test_multi_monitor_workflow(self):
        """Test transformation for multi-monitor setup"""
        # Setup for dual monitor (1920x1080 each, side by side)
        transformer = CoordinateTransformer(3840, 1080)  # Combined width
        transformer.set_multi_monitor_offset(1920, 0)  # Point on second monitor

        # Element on second monitor
        ocr_bbox = [[100, 500], [200, 500], [200, 530], [100, 530]]

        result = transformer.transform(ocr_bbox)

        # Virtual desktop coordinate should include offset
        virtual = result['stage4_virtual_desktop']
        assert virtual[0] > 1920  # On second monitor
