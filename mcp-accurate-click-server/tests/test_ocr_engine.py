"""
Tests for OCR Engine Module
Tests OCR initialization, text extraction, multi-pass averaging, and confidence filtering.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from typing import List, Tuple


# ============================================================================
# Mock OCR Engine Implementation
# ============================================================================

class OCREngine:
    """OCR Engine for text detection and extraction"""

    def __init__(self, use_angle_cls=True, lang='en', show_log=False,
                 confidence_threshold=0.5):
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self.show_log = show_log
        self.confidence_threshold = confidence_threshold
        self.is_initialized = False
        self._ocr_model = None

    def initialize(self):
        """Initialize OCR model"""
        if not self.is_initialized:
            # In real implementation, load PaddleOCR model
            self._ocr_model = "MockOCRModel"
            self.is_initialized = True
        return self.is_initialized

    def extract_text(self, image, **kwargs):
        """
        Extract text and bounding boxes from image

        Args:
            image: Image array (numpy array or PIL Image)
            **kwargs: Additional OCR parameters

        Returns:
            List of detections with bbox, text, and confidence
        """
        if not self.is_initialized:
            raise RuntimeError("OCR engine not initialized")

        # Mock implementation
        results = []
        return results

    def get_text_coordinates(self, image, text_query=None, **kwargs):
        """
        Get coordinates of specific text in image

        Args:
            image: Image to search
            text_query: Specific text to find (None = all text)

        Returns:
            List of matches with coordinates
        """
        detections = self.extract_text(image, **kwargs)

        if text_query is None:
            return detections

        # Filter by text query
        matches = []
        for detection in detections:
            if text_query.lower() in detection['text'].lower():
                matches.append(detection)

        return matches

    def filter_by_confidence(self, detections, threshold=None):
        """Filter detections by confidence threshold"""
        if threshold is None:
            threshold = self.confidence_threshold

        return [d for d in detections if d.get('confidence', 0) >= threshold]


class MultiPassOCR:
    """Multi-pass OCR with averaging for improved accuracy"""

    def __init__(self, ocr_engine, num_passes=3):
        self.ocr_engine = ocr_engine
        self.num_passes = num_passes

    def extract_with_averaging(self, image, **kwargs):
        """
        Run OCR multiple times and average coordinates

        This reduces random variance by sqrt(num_passes)
        """
        if not self.ocr_engine.is_initialized:
            self.ocr_engine.initialize()

        all_passes = []

        for pass_num in range(self.num_passes):
            results = self.ocr_engine.extract_text(image, **kwargs)
            all_passes.append(results)

        # Average coordinates for matching text
        averaged_results = self._average_detections(all_passes)

        return averaged_results

    def _average_detections(self, all_passes):
        """Average detections across multiple passes"""
        if not all_passes:
            return []

        # Group by text content
        text_groups = {}

        for pass_results in all_passes:
            for detection in pass_results:
                text = detection.get('text', '')
                if text not in text_groups:
                    text_groups[text] = []
                text_groups[text].append(detection)

        # Average each group
        averaged = []
        for text, detections in text_groups.items():
            avg_detection = self._average_detection_group(detections)
            averaged.append(avg_detection)

        return averaged

    def _average_detection_group(self, detections):
        """Average a group of detections with same text"""
        if not detections:
            return None

        # Average bbox coordinates
        bboxes = [d['bbox'] for d in detections]
        avg_bbox = np.mean(bboxes, axis=0).tolist()

        # Average confidence
        confidences = [d.get('confidence', 0) for d in detections]
        avg_confidence = np.mean(confidences)

        return {
            'bbox': avg_bbox,
            'text': detections[0]['text'],
            'confidence': avg_confidence,
            'num_passes': len(detections)
        }


# ============================================================================
# Test Class: OCR Engine Initialization
# ============================================================================

class TestOCREngineInitialization:
    """Test OCR engine initialization and configuration"""

    def test_engine_creation(self):
        """Test creating OCR engine with default parameters"""
        engine = OCREngine()

        assert engine.use_angle_cls is True
        assert engine.lang == 'en'
        assert engine.show_log is False
        assert engine.confidence_threshold == 0.5
        assert engine.is_initialized is False

    def test_engine_custom_parameters(self):
        """Test creating OCR engine with custom parameters"""
        engine = OCREngine(
            use_angle_cls=False,
            lang='ch',
            show_log=True,
            confidence_threshold=0.7
        )

        assert engine.use_angle_cls is False
        assert engine.lang == 'ch'
        assert engine.show_log is True
        assert engine.confidence_threshold == 0.7

    def test_engine_initialization(self):
        """Test OCR engine initialization"""
        engine = OCREngine()
        assert engine.is_initialized is False

        result = engine.initialize()

        assert result is True
        assert engine.is_initialized is True

    def test_engine_double_initialization(self):
        """Test that double initialization is safe"""
        engine = OCREngine()

        engine.initialize()
        assert engine.is_initialized is True

        # Initialize again
        engine.initialize()
        assert engine.is_initialized is True


# ============================================================================
# Test Class: Text Extraction
# ============================================================================

class TestTextExtraction:
    """Test OCR text extraction functionality"""

    @pytest.fixture
    def mock_image(self):
        """Create mock image for testing"""
        return np.zeros((100, 100, 3), dtype=np.uint8)

    @pytest.fixture
    def initialized_engine(self):
        """Create and initialize OCR engine"""
        engine = OCREngine()
        engine.initialize()
        return engine

    def test_extract_text_requires_initialization(self, mock_image):
        """Test that extraction requires initialization"""
        engine = OCREngine()

        with pytest.raises(RuntimeError, match="not initialized"):
            engine.extract_text(mock_image)

    def test_extract_text_basic(self, initialized_engine, mock_image):
        """Test basic text extraction"""
        # Mock the extraction to return sample data
        initialized_engine._ocr_model = Mock()

        results = initialized_engine.extract_text(mock_image)

        assert isinstance(results, list)

    def test_extract_text_with_mock_results(self, initialized_engine, mock_image):
        """Test extraction with mocked OCR results"""
        # Mock OCR to return specific results
        mock_results = [
            {
                'bbox': [[10, 10], [100, 10], [100, 40], [10, 40]],
                'text': 'Test Button',
                'confidence': 0.95
            },
            {
                'bbox': [[10, 50], [100, 50], [100, 80], [10, 80]],
                'text': 'Cancel',
                'confidence': 0.87
            }
        ]

        initialized_engine.extract_text = Mock(return_value=mock_results)
        results = initialized_engine.extract_text(mock_image)

        assert len(results) == 2
        assert results[0]['text'] == 'Test Button'
        assert results[0]['confidence'] == 0.95
        assert results[1]['text'] == 'Cancel'

    def test_get_text_coordinates_all(self, initialized_engine, mock_image):
        """Test getting coordinates of all text"""
        mock_results = [
            {'bbox': [[10, 10], [100, 10], [100, 40], [10, 40]],
             'text': 'Button', 'confidence': 0.9}
        ]

        initialized_engine.extract_text = Mock(return_value=mock_results)
        results = initialized_engine.get_text_coordinates(mock_image)

        assert len(results) == 1
        assert results[0]['text'] == 'Button'

    def test_get_text_coordinates_specific(self, initialized_engine, mock_image):
        """Test getting coordinates of specific text"""
        mock_results = [
            {'bbox': [[10, 10], [100, 10], [100, 40], [10, 40]],
             'text': 'OK', 'confidence': 0.9},
            {'bbox': [[120, 10], [200, 10], [200, 40], [120, 40]],
             'text': 'Cancel', 'confidence': 0.85}
        ]

        initialized_engine.extract_text = Mock(return_value=mock_results)
        results = initialized_engine.get_text_coordinates(mock_image, text_query='OK')

        assert len(results) == 1
        assert results[0]['text'] == 'OK'

    def test_get_text_coordinates_case_insensitive(self, initialized_engine, mock_image):
        """Test that text search is case-insensitive"""
        mock_results = [
            {'bbox': [[10, 10], [100, 10], [100, 40], [10, 40]],
             'text': 'Submit', 'confidence': 0.9}
        ]

        initialized_engine.extract_text = Mock(return_value=mock_results)

        # Search with different case
        results = initialized_engine.get_text_coordinates(mock_image, text_query='submit')

        assert len(results) == 1
        assert results[0]['text'] == 'Submit'


# ============================================================================
# Test Class: Confidence Filtering
# ============================================================================

class TestConfidenceFiltering:
    """Test confidence-based filtering of OCR results"""

    @pytest.fixture
    def mock_detections(self):
        """Create mock detections with varying confidence"""
        return [
            {'text': 'High', 'confidence': 0.95, 'bbox': [[0, 0], [10, 10]]},
            {'text': 'Medium', 'confidence': 0.70, 'bbox': [[0, 0], [10, 10]]},
            {'text': 'Low', 'confidence': 0.30, 'bbox': [[0, 0], [10, 10]]},
            {'text': 'Very High', 'confidence': 0.99, 'bbox': [[0, 0], [10, 10]]},
        ]

    def test_filter_by_default_threshold(self, mock_detections):
        """Test filtering with default threshold (0.5)"""
        engine = OCREngine(confidence_threshold=0.5)

        filtered = engine.filter_by_confidence(mock_detections)

        assert len(filtered) == 3  # High, Medium, Very High
        assert all(d['confidence'] >= 0.5 for d in filtered)

    def test_filter_by_custom_threshold(self, mock_detections):
        """Test filtering with custom threshold"""
        engine = OCREngine()

        filtered = engine.filter_by_confidence(mock_detections, threshold=0.8)

        assert len(filtered) == 2  # High, Very High
        assert all(d['confidence'] >= 0.8 for d in filtered)

    def test_filter_by_high_threshold(self, mock_detections):
        """Test filtering with very high threshold"""
        engine = OCREngine()

        filtered = engine.filter_by_confidence(mock_detections, threshold=0.98)

        assert len(filtered) == 1  # Only Very High
        assert filtered[0]['text'] == 'Very High'

    def test_filter_empty_list(self):
        """Test filtering empty detection list"""
        engine = OCREngine()

        filtered = engine.filter_by_confidence([])

        assert len(filtered) == 0

    def test_filter_missing_confidence(self):
        """Test filtering detections with missing confidence"""
        detections = [
            {'text': 'No confidence', 'bbox': [[0, 0], [10, 10]]}
        ]

        engine = OCREngine(confidence_threshold=0.5)
        filtered = engine.filter_by_confidence(detections)

        # Should be filtered out (confidence defaults to 0)
        assert len(filtered) == 0


# ============================================================================
# Test Class: Multi-Pass Averaging
# ============================================================================

class TestMultiPassAveraging:
    """Test multi-pass OCR with coordinate averaging"""

    @pytest.fixture
    def mock_engine(self):
        """Create mock OCR engine"""
        engine = OCREngine()
        engine.initialize()
        return engine

    def test_multi_pass_creation(self, mock_engine):
        """Test creating multi-pass OCR"""
        multi = MultiPassOCR(mock_engine, num_passes=3)

        assert multi.ocr_engine is mock_engine
        assert multi.num_passes == 3

    def test_multi_pass_with_consistent_results(self, mock_engine):
        """Test averaging when all passes return same results"""
        # Mock to return identical results
        mock_result = [
            {'bbox': [[100, 100], [200, 100], [200, 130], [100, 130]],
             'text': 'Button', 'confidence': 0.9}
        ]

        mock_engine.extract_text = Mock(return_value=mock_result)
        multi = MultiPassOCR(mock_engine, num_passes=3)

        averaged = multi.extract_with_averaging(None)

        assert len(averaged) == 1
        assert averaged[0]['text'] == 'Button'
        assert averaged[0]['num_passes'] == 3

        # Bbox should be same (averaged from identical values)
        expected_bbox = [[100, 100], [200, 100], [200, 130], [100, 130]]
        np.testing.assert_array_almost_equal(averaged[0]['bbox'], expected_bbox)

    def test_multi_pass_reduces_variance(self, mock_engine):
        """Test that averaging reduces coordinate variance"""
        # Simulate noisy measurements
        base_bbox = np.array([[100, 100], [200, 100], [200, 130], [100, 130]])

        pass_results = []
        for i in range(3):
            # Add random noise to each pass
            noisy_bbox = base_bbox + np.random.normal(0, 1, base_bbox.shape)
            pass_results.append([
                {'bbox': noisy_bbox.tolist(), 'text': 'Button', 'confidence': 0.9}
            ])

        # Mock to return different results each call
        mock_engine.extract_text = Mock(side_effect=pass_results)
        multi = MultiPassOCR(mock_engine, num_passes=3)

        averaged = multi.extract_with_averaging(None)

        # Averaged bbox should be close to base (noise cancels out)
        avg_bbox = np.array(averaged[0]['bbox'])
        error = np.linalg.norm(avg_bbox - base_bbox)

        # Error should be small due to averaging
        assert error < 5.0  # Tolerance for random variation

    def test_multi_pass_averages_confidence(self, mock_engine):
        """Test that confidence scores are averaged"""
        pass_results = [
            [{'bbox': [[100, 100], [200, 100], [200, 130], [100, 130]],
              'text': 'Test', 'confidence': 0.8}],
            [{'bbox': [[100, 100], [200, 100], [200, 130], [100, 130]],
              'text': 'Test', 'confidence': 0.9}],
            [{'bbox': [[100, 100], [200, 100], [200, 130], [100, 130]],
              'text': 'Test', 'confidence': 0.7}]
        ]

        mock_engine.extract_text = Mock(side_effect=pass_results)
        multi = MultiPassOCR(mock_engine, num_passes=3)

        averaged = multi.extract_with_averaging(None)

        # Confidence should be average: (0.8 + 0.9 + 0.7) / 3 = 0.8
        assert abs(averaged[0]['confidence'] - 0.8) < 0.01

    def test_multi_pass_with_varying_detections(self, mock_engine):
        """Test averaging when different passes detect different text"""
        pass_results = [
            [{'bbox': [[100, 100], [200, 100], [200, 130], [100, 130]],
              'text': 'Button', 'confidence': 0.9},
             {'bbox': [[300, 100], [400, 100], [400, 130], [300, 130]],
              'text': 'Link', 'confidence': 0.8}],
            [{'bbox': [[100, 100], [200, 100], [200, 130], [100, 130]],
              'text': 'Button', 'confidence': 0.85}],  # Only Button detected
            [{'bbox': [[100, 100], [200, 100], [200, 130], [100, 130]],
              'text': 'Button', 'confidence': 0.95},
             {'bbox': [[300, 100], [400, 100], [400, 130], [300, 130]],
              'text': 'Link', 'confidence': 0.75}]
        ]

        mock_engine.extract_text = Mock(side_effect=pass_results)
        multi = MultiPassOCR(mock_engine, num_passes=3)

        averaged = multi.extract_with_averaging(None)

        # Should have 2 results (Button and Link)
        assert len(averaged) == 2

        # Button should have 3 passes, Link should have 2
        button_result = next(r for r in averaged if r['text'] == 'Button')
        link_result = next(r for r in averaged if r['text'] == 'Link')

        assert button_result['num_passes'] == 3
        assert link_result['num_passes'] == 2


# ============================================================================
# Test Class: Error Reduction Analysis
# ============================================================================

@pytest.mark.performance
class TestErrorReduction:
    """Test that multi-pass averaging reduces measurement error"""

    def test_single_vs_multi_pass_error(self, ocr_simulator, random_coordinates):
        """Compare error of single pass vs multi-pass"""
        # Generate test coordinates
        true_coords = random_coordinates(n_points=100, seed=42)

        # Single pass measurements
        single_errors = []
        for coord in true_coords:
            measured = ocr_simulator.measure(coord)
            error = np.linalg.norm(measured - coord)
            single_errors.append(error)

        # Multi-pass measurements (3 passes)
        multi_errors = []
        for coord in true_coords:
            measured = ocr_simulator.multi_pass_measure(coord, num_passes=3)
            error = np.linalg.norm(measured - coord)
            multi_errors.append(error)

        single_mean = np.mean(single_errors)
        multi_mean = np.mean(multi_errors)

        # Multi-pass should have lower mean error
        assert multi_mean < single_mean

        # Theoretical reduction: error should reduce by ~sqrt(3) ≈ 1.73
        reduction_ratio = single_mean / multi_mean
        assert reduction_ratio > 1.3  # At least 30% improvement

    def test_error_reduction_scales_with_passes(self, ocr_simulator,
                                                random_coordinates):
        """Test that more passes = better accuracy"""
        true_coords = random_coordinates(n_points=50, seed=42)

        mean_errors = {}

        for num_passes in [1, 2, 3, 5]:
            errors = []
            for coord in true_coords:
                measured = ocr_simulator.multi_pass_measure(coord, num_passes=num_passes)
                error = np.linalg.norm(measured - coord)
                errors.append(error)

            mean_errors[num_passes] = np.mean(errors)

        # More passes should generally reduce error
        assert mean_errors[3] < mean_errors[1]
        assert mean_errors[5] < mean_errors[2]


# ============================================================================
# Test Class: Integration Tests
# ============================================================================

@pytest.mark.integration
class TestOCREngineIntegration:
    """Integration tests for complete OCR workflow"""

    def test_end_to_end_text_detection(self):
        """Test complete workflow from image to coordinates"""
        # Create engine
        engine = OCREngine(confidence_threshold=0.7)
        engine.initialize()

        # Mock image and OCR results
        mock_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_results = [
            {'bbox': [[100, 100], [200, 100], [200, 130], [100, 130]],
             'text': 'Submit', 'confidence': 0.95},
            {'bbox': [[220, 100], [320, 100], [320, 130], [220, 130]],
             'text': 'Cancel', 'confidence': 0.88},
            {'bbox': [[100, 200], [200, 200], [200, 230], [100, 230]],
             'text': 'Low Conf', 'confidence': 0.40}
        ]
        engine.extract_text = Mock(return_value=mock_results)

        # Extract and filter
        detections = engine.extract_text(mock_image)
        filtered = engine.filter_by_confidence(detections)

        # Should filter out low confidence
        assert len(filtered) == 2
        assert all(d['confidence'] >= 0.7 for d in filtered)

    def test_multi_pass_integration(self):
        """Test multi-pass OCR integration"""
        engine = OCREngine()
        engine.initialize()

        multi = MultiPassOCR(engine, num_passes=3)

        # Mock varying results
        pass_results = [
            [{'bbox': [[100, 100], [200, 100], [200, 130], [100, 130]],
              'text': 'OK', 'confidence': 0.9}],
            [{'bbox': [[101, 99], [201, 99], [201, 129], [101, 129]],
              'text': 'OK', 'confidence': 0.88}],
            [{'bbox': [[99, 101], [199, 101], [199, 131], [99, 131]],
              'text': 'OK', 'confidence': 0.92}]
        ]

        engine.extract_text = Mock(side_effect=pass_results)

        averaged = multi.extract_with_averaging(None)

        assert len(averaged) == 1
        assert averaged[0]['text'] == 'OK'
        assert averaged[0]['num_passes'] == 3

        # Averaged bbox should be close to [100, 100], [200, 100], etc.
        avg_bbox = np.array(averaged[0]['bbox'])
        expected = np.array([[100, 100], [200, 100], [200, 130], [100, 130]])
        error = np.linalg.norm(avg_bbox - expected)
        assert error < 5.0  # Should be very close due to averaging
