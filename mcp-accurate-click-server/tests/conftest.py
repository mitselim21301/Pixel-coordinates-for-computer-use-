"""
Pytest Configuration and Shared Fixtures
Provides common test utilities, mock data generators, and fixtures for the test suite.
"""

import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock


# ============================================================================
# Configuration Classes
# ============================================================================

@dataclass
class TestConfig:
    """Test configuration constants"""
    screen_width: int = 1920
    screen_height: int = 1080
    dpi_scale: float = 1.0
    accuracy_threshold: float = 2.0
    target_success_rate: float = 0.99

    # OCR simulation parameters
    ocr_systematic_bias: Tuple[float, float] = (3.5, -2.8)
    ocr_random_error_std: float = 0.55

    # Calibration parameters
    calibration_points: int = 30
    regional_grid: Tuple[int, int] = (2, 2)
    ocr_passes: int = 3


@dataclass
class MockOCRResult:
    """Mock OCR detection result"""
    bbox: List[List[float]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    text: str
    confidence: float

    def get_center(self) -> Tuple[float, float]:
        """Get center of bounding box"""
        x_coords = [p[0] for p in self.bbox]
        y_coords = [p[1] for p in self.bbox]
        return (sum(x_coords) / 4, sum(y_coords) / 4)


# ============================================================================
# Fixtures - Configuration
# ============================================================================

@pytest.fixture
def test_config():
    """Provide default test configuration"""
    return TestConfig()


@pytest.fixture
def screen_dimensions(test_config):
    """Provide screen dimensions"""
    return (test_config.screen_width, test_config.screen_height)


@pytest.fixture
def dpi_scale(test_config):
    """Provide DPI scale factor"""
    return test_config.dpi_scale


# ============================================================================
# Fixtures - Temporary Files and Directories
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_calibration_file(temp_dir):
    """Provide path to temporary calibration file"""
    return temp_dir / "test_calibration.json"


@pytest.fixture
def temp_config_file(temp_dir):
    """Provide path to temporary config file"""
    return temp_dir / "test_config.json"


# ============================================================================
# Fixtures - Mock OCR Data
# ============================================================================

@pytest.fixture
def mock_ocr_result():
    """Create a single mock OCR result"""
    def _create_result(center_x=960, center_y=540, width=100, height=30,
                       text="Button", confidence=0.95):
        """Create OCR result centered at given position"""
        half_w = width / 2
        half_h = height / 2

        bbox = [
            [center_x - half_w, center_y - half_h],  # top-left
            [center_x + half_w, center_y - half_h],  # top-right
            [center_x + half_w, center_y + half_h],  # bottom-right
            [center_x - half_w, center_y + half_h],  # bottom-left
        ]

        return MockOCRResult(bbox=bbox, text=text, confidence=confidence)

    return _create_result


@pytest.fixture
def mock_ocr_results(mock_ocr_result, test_config):
    """Generate multiple mock OCR results across the screen"""
    results = []

    # Create a grid of mock OCR results
    for x in np.linspace(200, test_config.screen_width - 200, 5):
        for y in np.linspace(150, test_config.screen_height - 150, 4):
            result = mock_ocr_result(
                center_x=x,
                center_y=y,
                text=f"Element_{int(x)}_{int(y)}",
                confidence=np.random.uniform(0.85, 0.99)
            )
            results.append(result)

    return results


# ============================================================================
# Fixtures - Coordinate Generation
# ============================================================================

@pytest.fixture
def random_coordinates(test_config):
    """Generate random coordinates within screen bounds"""
    def _generate(n_points=10, margin=100, seed=42):
        """
        Generate random screen coordinates

        Args:
            n_points: Number of points to generate
            margin: Margin from screen edges
            seed: Random seed for reproducibility
        """
        np.random.seed(seed)
        coords = np.random.uniform(
            [margin, margin],
            [test_config.screen_width - margin, test_config.screen_height - margin],
            (n_points, 2)
        )
        return coords

    return _generate


@pytest.fixture
def grid_coordinates(test_config):
    """Generate coordinates in a regular grid pattern"""
    def _generate(grid_size=(5, 4), margin=150):
        """
        Generate grid of coordinates

        Args:
            grid_size: (cols, rows) grid dimensions
            margin: Margin from screen edges
        """
        cols, rows = grid_size
        x_coords = np.linspace(
            margin,
            test_config.screen_width - margin,
            cols
        )
        y_coords = np.linspace(
            margin,
            test_config.screen_height - margin,
            rows
        )

        coords = []
        for x in x_coords:
            for y in y_coords:
                coords.append([x, y])

        return np.array(coords)

    return _generate


# ============================================================================
# Fixtures - OCR Simulation
# ============================================================================

@pytest.fixture
def ocr_simulator(test_config):
    """Simulate OCR measurements with realistic errors"""
    class OCRSimulator:
        def __init__(self, config):
            self.config = config
            self.systematic_bias = np.array(config.ocr_systematic_bias)
            self.random_error_std = config.ocr_random_error_std

        def measure(self, true_coord: np.ndarray,
                   add_bias: bool = True,
                   add_noise: bool = True) -> np.ndarray:
            """Simulate OCR measurement of a coordinate"""
            measured = true_coord.copy()

            if add_bias:
                measured = measured + self.systematic_bias

            if add_noise:
                measured = measured + np.random.normal(
                    0, self.random_error_std, measured.shape
                )

            return measured

        def measure_batch(self, true_coords: np.ndarray,
                         **kwargs) -> np.ndarray:
            """Measure multiple coordinates"""
            return np.array([
                self.measure(coord, **kwargs) for coord in true_coords
            ])

        def multi_pass_measure(self, true_coord: np.ndarray,
                              num_passes: int = 3) -> np.ndarray:
            """Simulate multi-pass OCR with averaging"""
            measurements = []
            for _ in range(num_passes):
                measured = self.measure(true_coord)
                measurements.append(measured)

            # Average reduces variance
            return np.mean(measurements, axis=0)

    return OCRSimulator(test_config)


# ============================================================================
# Fixtures - Mock Components
# ============================================================================

@pytest.fixture
def mock_ocr_engine():
    """Mock OCR engine for testing"""
    mock = MagicMock()
    mock.is_initialized = True
    mock.confidence_threshold = 0.5

    def mock_extract(image, **kwargs):
        # Return mock results based on image
        return [
            MockOCRResult(
                bbox=[[100, 100], [200, 100], [200, 130], [100, 130]],
                text="Test",
                confidence=0.95
            )
        ]

    mock.extract_text = Mock(side_effect=mock_extract)
    return mock


@pytest.fixture
def mock_calibration():
    """Mock calibration system"""
    class MockCalibration:
        def __init__(self):
            self.is_calibrated = False
            self.offset = np.array([0.0, 0.0])

        def calibrate(self, measured, true):
            if len(measured) < 3:
                raise ValueError("Calibration requires at least 3 points")
            self.offset = np.mean(measured - true, axis=0)
            self.is_calibrated = True

        def correct(self, measured):
            if not self.is_calibrated:
                return measured
            return measured - self.offset

        def correct_batch(self, measured_batch):
            """Correct multiple coordinates at once"""
            if not self.is_calibrated:
                return measured_batch
            return measured_batch - self.offset

        def save(self, filepath):
            data = {
                'is_calibrated': self.is_calibrated,
                'offset': self.offset.tolist()
            }
            with open(filepath, 'w') as f:
                json.dump(data, f)

        def load(self, filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.is_calibrated = data['is_calibrated']
            self.offset = np.array(data['offset'])

    return MockCalibration()


@pytest.fixture
def mock_coordinate_transformer():
    """Mock coordinate transformer"""
    class MockTransformer:
        def __init__(self):
            self.screen_width = 1920
            self.screen_height = 1080
            self.dpi_scale = 1.0

        def physical_to_logical(self, coords):
            """Convert physical to logical pixels"""
            return coords / self.dpi_scale

        def logical_to_physical(self, coords):
            """Convert logical to physical pixels"""
            return coords * self.dpi_scale

        def to_sendinput(self, coords):
            """Convert to SendInput normalized coordinates (0-65535)"""
            x, y = coords
            norm_x = int((x / self.screen_width) * 65535)
            norm_y = int((y / self.screen_height) * 65535)
            return (norm_x, norm_y)

        def from_sendinput(self, norm_coords):
            """Convert from SendInput coordinates back to pixels"""
            norm_x, norm_y = norm_coords
            x = (norm_x / 65535) * self.screen_width
            y = (norm_y / 65535) * self.screen_height
            return (x, y)

    return MockTransformer()


@pytest.fixture
def mock_click_executor():
    """Mock click executor that doesn't actually click"""
    from dataclasses import dataclass

    @dataclass
    class ClickResult:
        """Result of a click operation"""
        x: float
        y: float
        button: str = 'left'
        double: bool = False
        success: bool = True

    class MockClickExecutor:
        def __init__(self):
            self.last_click = None
            self.click_count = 0
            self.clicks_history = []

        def click(self, x, y, button='left', double=False, auto_clamp=False):
            """Record click without executing"""
            result = ClickResult(
                x=x,
                y=y,
                button=button,
                double=double,
                success=True
            )
            self.last_click = result
            self.click_count += 1
            self.clicks_history.append(result)
            return result

        def get_click_count(self):
            """Get total click count"""
            return self.click_count

        def reset(self):
            """Reset click history"""
            self.last_click = None
            self.click_count = 0
            self.clicks_history = []

    return MockClickExecutor()


# ============================================================================
# Fixtures - Window Simulation
# ============================================================================

@pytest.fixture
def mock_windows():
    """Create mock window configurations for testing"""
    from dataclasses import dataclass

    @dataclass
    class MockWindow:
        x: int
        y: int
        width: int
        height: int
        title: str

        def contains_point(self, px, py):
            return (self.x <= px <= self.x + self.width and
                   self.y <= py <= self.y + self.height)

    windows = [
        MockWindow(50, 50, 400, 300, "Small Dialog"),
        MockWindow(560, 240, 800, 600, "Main Window"),
        MockWindow(100, 100, 1200, 900, "Large Window"),
    ]

    return windows


# ============================================================================
# Fixtures - Performance Benchmarking
# ============================================================================

@pytest.fixture
def benchmark_timer():
    """Simple timing utility for performance tests"""
    import time

    class BenchmarkTimer:
        def __init__(self):
            self.times = {}

        def time_function(self, name, func, *args, **kwargs):
            """Time a function call"""
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start

            if name not in self.times:
                self.times[name] = []
            self.times[name].append(elapsed)

            return result, elapsed

        def get_stats(self, name):
            """Get timing statistics"""
            if name not in self.times:
                return None

            times = self.times[name]
            return {
                'mean': np.mean(times),
                'median': np.median(times),
                'std': np.std(times),
                'min': np.min(times),
                'max': np.max(times),
                'count': len(times)
            }

        def print_stats(self, name):
            """Print timing statistics"""
            stats = self.get_stats(name)
            if stats:
                print(f"\nBenchmark: {name}")
                print(f"  Mean:   {stats['mean']*1000:.2f} ms")
                print(f"  Median: {stats['median']*1000:.2f} ms")
                print(f"  Std:    {stats['std']*1000:.2f} ms")
                print(f"  Range:  [{stats['min']*1000:.2f}, {stats['max']*1000:.2f}] ms")
                print(f"  Count:  {stats['count']}")

    return BenchmarkTimer()


# ============================================================================
# Utility Functions
# ============================================================================

@pytest.fixture
def assert_accuracy():
    """Helper to assert coordinate accuracy"""
    def _assert(measured, true, threshold=2.0):
        """Assert that measured coordinates are within threshold of true"""
        error = np.linalg.norm(np.array(measured) - np.array(true))
        assert error <= threshold, (
            f"Coordinate error {error:.3f}px exceeds threshold {threshold}px. "
            f"Measured: {measured}, True: {true}"
        )
    return _assert


@pytest.fixture
def calculate_accuracy_metrics():
    """Calculate standard accuracy metrics"""
    def _calculate(true_coords, measured_coords):
        """
        Calculate accuracy metrics

        Returns:
            dict with mean_error, median_error, std_error, max_error,
            within_1px, within_2px, within_5px
        """
        errors = np.linalg.norm(
            np.array(true_coords) - np.array(measured_coords),
            axis=1
        )

        return {
            'mean_error': float(np.mean(errors)),
            'median_error': float(np.median(errors)),
            'std_error': float(np.std(errors)),
            'max_error': float(np.max(errors)),
            'min_error': float(np.min(errors)),
            'within_1px': float(np.sum(errors <= 1.0) / len(errors)),
            'within_2px': float(np.sum(errors <= 2.0) / len(errors)),
            'within_5px': float(np.sum(errors <= 5.0) / len(errors)),
            'num_samples': len(errors)
        }

    return _calculate


# ============================================================================
# Session-Level Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_results_dir():
    """Create directory for test results"""
    results_dir = Path(__file__).parent / "test_results"
    results_dir.mkdir(exist_ok=True)
    return results_dir


# ============================================================================
# Markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks"
    )
    config.addinivalue_line(
        "markers", "requires_ocr: marks tests that require OCR models"
    )
