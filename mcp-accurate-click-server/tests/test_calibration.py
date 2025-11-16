"""
Tests for Calibration System
Tests simple calibration, regional calibration, save/load functionality, and accuracy validation.

Based on test_ultra_accuracy.py and test_simple_accuracy.py implementations.
"""

import pytest
import numpy as np
import json
from pathlib import Path
from typing import Tuple, Dict
from dataclasses import dataclass, asdict


# ============================================================================
# Calibration System Implementation
# ============================================================================

class SimpleCalibration:
    """Simple offset-based calibration"""

    def __init__(self, screen_width=1920, screen_height=1080):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset = None
        self.is_calibrated = False
        self.calibration_metadata = {}

    def calibrate(self, measured_points: np.ndarray, true_points: np.ndarray):
        """
        Compute calibration offset from measured and true points

        Args:
            measured_points: Nx2 array of measured coordinates
            true_points: Nx2 array of true coordinates
        """
        if len(measured_points) != len(true_points):
            raise ValueError("Measured and true points must have same length")

        if len(measured_points) < 3:
            raise ValueError("Need at least 3 calibration points")

        # Compute mean offset
        self.offset = np.mean(measured_points - true_points, axis=0)
        self.is_calibrated = True

        # Store metadata
        self.calibration_metadata = {
            'num_points': len(measured_points),
            'mean_offset': self.offset.tolist(),
            'calibration_error': float(np.mean(np.linalg.norm(
                self.correct_batch(measured_points) - true_points, axis=1
            )))
        }

    def correct(self, measured: np.ndarray) -> np.ndarray:
        """Apply calibration correction to a single point"""
        if not self.is_calibrated:
            return measured
        return measured - self.offset

    def correct_batch(self, measured_points: np.ndarray) -> np.ndarray:
        """Apply calibration correction to multiple points"""
        if not self.is_calibrated:
            return measured_points
        return measured_points - self.offset

    def save(self, filepath):
        """Save calibration to file"""
        if not self.is_calibrated:
            raise RuntimeError("Cannot save uncalibrated system")

        data = {
            'screen_width': self.screen_width,
            'screen_height': self.screen_height,
            'offset': self.offset.tolist(),
            'is_calibrated': self.is_calibrated,
            'metadata': self.calibration_metadata
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self, filepath):
        """Load calibration from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.screen_width = data['screen_width']
        self.screen_height = data['screen_height']
        self.offset = np.array(data['offset'])
        self.is_calibrated = data['is_calibrated']
        self.calibration_metadata = data.get('metadata', {})

    def get_stats(self) -> Dict:
        """Get calibration statistics"""
        if not self.is_calibrated:
            return {}

        return {
            'is_calibrated': self.is_calibrated,
            'offset_x': float(self.offset[0]),
            'offset_y': float(self.offset[1]),
            'offset_magnitude': float(np.linalg.norm(self.offset)),
            **self.calibration_metadata
        }


class RegionalCalibration:
    """
    Per-region calibration for ultra-high accuracy
    Based on test_ultra_accuracy.py implementation
    """

    def __init__(self, grid_size: Tuple[int, int], screen_size: Tuple[int, int]):
        self.grid_rows, self.grid_cols = grid_size
        self.screen_width, self.screen_height = screen_size
        self.regional_offsets = {}
        self.is_calibrated = False
        self.calibration_metadata = {}

    def _get_region(self, x: float, y: float) -> Tuple[int, int]:
        """Determine which region a point belongs to"""
        region_width = self.screen_width / self.grid_cols
        region_height = self.screen_height / self.grid_rows

        col = min(int(x / region_width), self.grid_cols - 1)
        row = min(int(y / region_height), self.grid_rows - 1)

        return (row, col)

    def calibrate(self, measured_points: np.ndarray, true_points: np.ndarray):
        """Calibrate each region separately"""
        if len(measured_points) != len(true_points):
            raise ValueError("Measured and true points must have same length")

        # Group points by region
        region_points = {}

        for measured, true in zip(measured_points, true_points):
            region = self._get_region(true[0], true[1])

            if region not in region_points:
                region_points[region] = {'measured': [], 'true': []}

            region_points[region]['measured'].append(measured)
            region_points[region]['true'].append(true)

        # Compute offset for each region
        for region, points in region_points.items():
            measured = np.array(points['measured'])
            true = np.array(points['true'])

            # Compute mean offset for this region
            offset = np.mean(measured - true, axis=0)
            self.regional_offsets[region] = offset

        # Fill in any missing regions with global offset
        all_measured = np.array(measured_points)
        all_true = np.array(true_points)
        global_offset = np.mean(all_measured - all_true, axis=0)

        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                region = (row, col)
                if region not in self.regional_offsets:
                    self.regional_offsets[region] = global_offset

        self.is_calibrated = True

        # Store metadata
        self.calibration_metadata = {
            'num_points': len(measured_points),
            'num_regions': len(self.regional_offsets),
            'grid_size': [self.grid_rows, self.grid_cols],
            'global_offset': global_offset.tolist()
        }

    def correct(self, measured: np.ndarray) -> np.ndarray:
        """Apply regional correction to a single point"""
        if not self.is_calibrated:
            return measured

        x, y = measured
        region = self._get_region(x, y)
        offset = self.regional_offsets.get(region, np.array([0.0, 0.0]))

        return measured - offset

    def correct_batch(self, measured_points: np.ndarray) -> np.ndarray:
        """Apply regional correction to multiple points"""
        return np.array([self.correct(point) for point in measured_points])

    def save(self, filepath):
        """Save regional calibration to file"""
        if not self.is_calibrated:
            raise RuntimeError("Cannot save uncalibrated system")

        # Convert tuple keys to strings for JSON
        regional_offsets_json = {
            f"{row},{col}": offset.tolist()
            for (row, col), offset in self.regional_offsets.items()
        }

        data = {
            'screen_width': self.screen_width,
            'screen_height': self.screen_height,
            'grid_rows': self.grid_rows,
            'grid_cols': self.grid_cols,
            'regional_offsets': regional_offsets_json,
            'is_calibrated': self.is_calibrated,
            'metadata': self.calibration_metadata
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self, filepath):
        """Load regional calibration from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.screen_width = data['screen_width']
        self.screen_height = data['screen_height']
        self.grid_rows = data['grid_rows']
        self.grid_cols = data['grid_cols']
        self.is_calibrated = data['is_calibrated']
        self.calibration_metadata = data.get('metadata', {})

        # Convert string keys back to tuples
        self.regional_offsets = {}
        for key, offset in data['regional_offsets'].items():
            row, col = map(int, key.split(','))
            self.regional_offsets[(row, col)] = np.array(offset)

    def get_region_stats(self) -> Dict:
        """Get per-region calibration statistics"""
        if not self.is_calibrated:
            return {}

        stats = {}
        for region, offset in self.regional_offsets.items():
            stats[f"region_{region[0]}_{region[1]}"] = {
                'offset_x': float(offset[0]),
                'offset_y': float(offset[1]),
                'magnitude': float(np.linalg.norm(offset))
            }

        return stats


# ============================================================================
# Test Class: Simple Calibration
# ============================================================================

class TestSimpleCalibration:
    """Test simple offset-based calibration"""

    def test_calibration_creation(self):
        """Test creating calibration system"""
        cal = SimpleCalibration()

        assert cal.screen_width == 1920
        assert cal.screen_height == 1080
        assert cal.is_calibrated is False
        assert cal.offset is None

    def test_calibration_with_perfect_offset(self, random_coordinates):
        """Test calibration with constant offset"""
        cal = SimpleCalibration()

        # Generate points with known offset
        true_points = random_coordinates(n_points=30, seed=42)
        offset = np.array([5.0, -3.0])
        measured_points = true_points + offset

        # Calibrate
        cal.calibrate(measured_points, true_points)

        assert cal.is_calibrated is True

        # Offset should be recovered
        np.testing.assert_array_almost_equal(cal.offset, offset, decimal=10)

    def test_calibration_correction(self, random_coordinates):
        """Test that calibration correction works"""
        cal = SimpleCalibration()

        true_points = random_coordinates(n_points=30, seed=42)
        offset = np.array([3.5, -2.8])
        measured_points = true_points + offset

        cal.calibrate(measured_points, true_points)

        # Test correction on new point
        new_true = np.array([500, 400])
        new_measured = new_true + offset
        corrected = cal.correct(new_measured)

        np.testing.assert_array_almost_equal(corrected, new_true, decimal=10)

    def test_calibration_batch_correction(self, random_coordinates):
        """Test batch correction"""
        cal = SimpleCalibration()

        true_points = random_coordinates(n_points=30, seed=42)
        offset = np.array([3.5, -2.8])
        measured_points = true_points + offset

        cal.calibrate(measured_points, true_points)

        # Test batch correction
        test_points = random_coordinates(n_points=50, seed=99)
        test_measured = test_points + offset
        corrected = cal.correct_batch(test_measured)

        np.testing.assert_array_almost_equal(corrected, test_points, decimal=10)

    def test_calibration_requires_minimum_points(self, random_coordinates):
        """Test that calibration requires at least 3 points"""
        cal = SimpleCalibration()

        # Try with only 2 points
        true_points = random_coordinates(n_points=2)
        measured_points = true_points + np.array([1.0, 1.0])

        with pytest.raises(ValueError, match="at least 3"):
            cal.calibrate(measured_points, true_points)

    def test_calibration_point_mismatch(self, random_coordinates):
        """Test error when point counts don't match"""
        cal = SimpleCalibration()

        true_points = random_coordinates(n_points=10)
        measured_points = random_coordinates(n_points=20)

        with pytest.raises(ValueError, match="same length"):
            cal.calibrate(measured_points, true_points)

    def test_correction_before_calibration(self):
        """Test that correction returns unchanged value before calibration"""
        cal = SimpleCalibration()

        point = np.array([100, 200])
        corrected = cal.correct(point)

        np.testing.assert_array_equal(corrected, point)

    def test_calibration_with_noise(self, random_coordinates, ocr_simulator):
        """Test calibration with realistic OCR noise"""
        cal = SimpleCalibration()

        # Generate calibration points
        true_points = random_coordinates(n_points=30, seed=42)
        measured_points = ocr_simulator.measure_batch(true_points)

        # Calibrate
        cal.calibrate(measured_points, true_points)

        # Test on new points
        test_points = random_coordinates(n_points=100, seed=99)
        test_measured = ocr_simulator.measure_batch(test_points)
        corrected = cal.correct_batch(test_measured)

        # Compute errors
        errors = np.linalg.norm(corrected - test_points, axis=1)
        mean_error = np.mean(errors)

        # Should significantly reduce error (from ~4px to <1px)
        assert mean_error < 1.0

    def test_get_calibration_stats(self, random_coordinates):
        """Test getting calibration statistics"""
        cal = SimpleCalibration()

        true_points = random_coordinates(n_points=30)
        offset = np.array([3.5, -2.8])
        measured_points = true_points + offset

        cal.calibrate(measured_points, true_points)

        stats = cal.get_stats()

        assert stats['is_calibrated'] is True
        assert abs(stats['offset_x'] - 3.5) < 0.01
        assert abs(stats['offset_y'] - (-2.8)) < 0.01
        assert stats['num_points'] == 30


# ============================================================================
# Test Class: Regional Calibration
# ============================================================================

class TestRegionalCalibration:
    """Test regional (per-quadrant) calibration"""

    def test_regional_calibration_creation(self):
        """Test creating regional calibration"""
        cal = RegionalCalibration(
            grid_size=(2, 2),
            screen_size=(1920, 1080)
        )

        assert cal.grid_rows == 2
        assert cal.grid_cols == 2
        assert cal.is_calibrated is False

    def test_get_region(self):
        """Test region assignment for points"""
        cal = RegionalCalibration(
            grid_size=(2, 2),
            screen_size=(1920, 1080)
        )

        # Top-left region (0, 0)
        assert cal._get_region(100, 100) == (0, 0)

        # Top-right region (0, 1)
        assert cal._get_region(1500, 100) == (0, 1)

        # Bottom-left region (1, 0)
        assert cal._get_region(100, 800) == (1, 0)

        # Bottom-right region (1, 1)
        assert cal._get_region(1500, 800) == (1, 1)

    def test_regional_calibration_with_uniform_offset(self, grid_coordinates):
        """Test regional calibration with uniform offset across all regions"""
        cal = RegionalCalibration(
            grid_size=(2, 2),
            screen_size=(1920, 1080)
        )

        # Generate grid of calibration points
        true_points = grid_coordinates(grid_size=(10, 8), margin=100)
        offset = np.array([5.0, -3.0])
        measured_points = true_points + offset

        cal.calibrate(measured_points, true_points)

        assert cal.is_calibrated is True

        # All regions should have similar offsets
        for region, region_offset in cal.regional_offsets.items():
            np.testing.assert_array_almost_equal(
                region_offset, offset, decimal=0
            )

    def test_regional_calibration_with_varying_offsets(self):
        """Test regional calibration with different offset per region"""
        cal = RegionalCalibration(
            grid_size=(2, 2),
            screen_size=(1920, 1080)
        )

        # Create points with different offsets per region
        true_points = []
        measured_points = []

        # Region (0, 0) - offset [2, -1]
        for _ in range(10):
            pt = np.array([np.random.uniform(100, 900),
                          np.random.uniform(100, 500)])
            true_points.append(pt)
            measured_points.append(pt + np.array([2.0, -1.0]))

        # Region (0, 1) - offset [4, -3]
        for _ in range(10):
            pt = np.array([np.random.uniform(1000, 1800),
                          np.random.uniform(100, 500)])
            true_points.append(pt)
            measured_points.append(pt + np.array([4.0, -3.0]))

        # Region (1, 0) - offset [1, -2]
        for _ in range(10):
            pt = np.array([np.random.uniform(100, 900),
                          np.random.uniform(600, 1000)])
            true_points.append(pt)
            measured_points.append(pt + np.array([1.0, -2.0]))

        # Region (1, 1) - offset [5, -4]
        for _ in range(10):
            pt = np.array([np.random.uniform(1000, 1800),
                          np.random.uniform(600, 1000)])
            true_points.append(pt)
            measured_points.append(pt + np.array([5.0, -4.0]))

        true_points = np.array(true_points)
        measured_points = np.array(measured_points)

        cal.calibrate(measured_points, true_points)

        # Check that each region has correct offset
        assert abs(cal.regional_offsets[(0, 0)][0] - 2.0) < 0.5
        assert abs(cal.regional_offsets[(0, 1)][0] - 4.0) < 0.5
        assert abs(cal.regional_offsets[(1, 0)][0] - 1.0) < 0.5
        assert abs(cal.regional_offsets[(1, 1)][0] - 5.0) < 0.5

    def test_regional_correction(self):
        """Test that regional correction uses correct offset"""
        cal = RegionalCalibration(
            grid_size=(2, 2),
            screen_size=(1920, 1080)
        )

        # Manually set regional offsets
        cal.regional_offsets = {
            (0, 0): np.array([2.0, -1.0]),
            (0, 1): np.array([4.0, -3.0]),
            (1, 0): np.array([1.0, -2.0]),
            (1, 1): np.array([5.0, -4.0])
        }
        cal.is_calibrated = True

        # Test point in region (0, 0)
        point_00 = np.array([400, 300])
        corrected_00 = cal.correct(point_00)
        expected_00 = point_00 - np.array([2.0, -1.0])
        np.testing.assert_array_almost_equal(corrected_00, expected_00)

        # Test point in region (1, 1)
        point_11 = np.array([1500, 800])
        corrected_11 = cal.correct(point_11)
        expected_11 = point_11 - np.array([5.0, -4.0])
        np.testing.assert_array_almost_equal(corrected_11, expected_11)

    def test_regional_vs_simple_accuracy(self, ocr_simulator):
        """Test that regional calibration improves accuracy over simple"""
        # Create points with spatially-varying error
        np.random.seed(42)

        true_points = []
        measured_points = []

        # Different systematic errors in different regions
        for _ in range(25):
            x, y = np.random.uniform([100, 100], [900, 500])
            true_points.append([x, y])
            measured_points.append([x + 2.0, y - 1.0])

        for _ in range(25):
            x, y = np.random.uniform([1000, 100], [1800, 500])
            true_points.append([x, y])
            measured_points.append([x + 6.0, y - 5.0])

        for _ in range(25):
            x, y = np.random.uniform([100, 600], [900, 1000])
            true_points.append([x, y])
            measured_points.append([x + 1.0, y - 3.0])

        for _ in range(25):
            x, y = np.random.uniform([1000, 600], [1800, 1000])
            true_points.append([x, y])
            measured_points.append([x + 8.0, y - 6.0])

        true_points = np.array(true_points)
        measured_points = np.array(measured_points)

        # Simple calibration
        simple_cal = SimpleCalibration()
        simple_cal.calibrate(measured_points, true_points)
        simple_corrected = simple_cal.correct_batch(measured_points)
        simple_errors = np.linalg.norm(simple_corrected - true_points, axis=1)
        simple_mean_error = np.mean(simple_errors)

        # Regional calibration
        regional_cal = RegionalCalibration((2, 2), (1920, 1080))
        regional_cal.calibrate(measured_points, true_points)
        regional_corrected = regional_cal.correct_batch(measured_points)
        regional_errors = np.linalg.norm(regional_corrected - true_points, axis=1)
        regional_mean_error = np.mean(regional_errors)

        # Regional should be significantly better
        assert regional_mean_error < simple_mean_error


# ============================================================================
# Test Class: Save/Load Calibration
# ============================================================================

class TestCalibrationPersistence:
    """Test saving and loading calibration data"""

    def test_save_simple_calibration(self, temp_calibration_file, random_coordinates):
        """Test saving simple calibration to file"""
        cal = SimpleCalibration()

        true_points = random_coordinates(n_points=30)
        measured_points = true_points + np.array([3.5, -2.8])

        cal.calibrate(measured_points, true_points)
        cal.save(temp_calibration_file)

        assert temp_calibration_file.exists()

    def test_load_simple_calibration(self, temp_calibration_file, random_coordinates):
        """Test loading simple calibration from file"""
        # Save calibration
        cal1 = SimpleCalibration()
        true_points = random_coordinates(n_points=30)
        measured_points = true_points + np.array([3.5, -2.8])
        cal1.calibrate(measured_points, true_points)
        cal1.save(temp_calibration_file)

        # Load in new instance
        cal2 = SimpleCalibration()
        cal2.load(temp_calibration_file)

        assert cal2.is_calibrated is True
        np.testing.assert_array_almost_equal(cal2.offset, cal1.offset)

    def test_save_before_calibration_fails(self, temp_calibration_file):
        """Test that saving before calibration raises error"""
        cal = SimpleCalibration()

        with pytest.raises(RuntimeError, match="uncalibrated"):
            cal.save(temp_calibration_file)

    def test_save_load_regional_calibration(self, temp_calibration_file,
                                           grid_coordinates):
        """Test saving and loading regional calibration"""
        # Save regional calibration
        cal1 = RegionalCalibration((2, 2), (1920, 1080))
        true_points = grid_coordinates(grid_size=(10, 8))
        measured_points = true_points + np.array([3.5, -2.8])
        cal1.calibrate(measured_points, true_points)
        cal1.save(temp_calibration_file)

        # Load in new instance
        cal2 = RegionalCalibration((2, 2), (1920, 1080))
        cal2.load(temp_calibration_file)

        assert cal2.is_calibrated is True
        assert cal2.grid_rows == 2
        assert cal2.grid_cols == 2

        # Check that offsets match
        for region in cal1.regional_offsets:
            np.testing.assert_array_almost_equal(
                cal2.regional_offsets[region],
                cal1.regional_offsets[region]
            )

    def test_loaded_calibration_works(self, temp_calibration_file, random_coordinates):
        """Test that loaded calibration produces same results"""
        # Calibrate and save
        cal1 = SimpleCalibration()
        true_points = random_coordinates(n_points=30, seed=42)
        measured_points = true_points + np.array([3.5, -2.8])
        cal1.calibrate(measured_points, true_points)
        cal1.save(temp_calibration_file)

        # Load and test
        cal2 = SimpleCalibration()
        cal2.load(temp_calibration_file)

        # Test correction produces same results
        test_point = np.array([500, 400])
        corrected1 = cal1.correct(test_point)
        corrected2 = cal2.correct(test_point)

        np.testing.assert_array_almost_equal(corrected1, corrected2)


# ============================================================================
# Test Class: Accuracy Validation
# ============================================================================

class TestCalibrationAccuracy:
    """Test calibration accuracy and validation"""

    def test_accuracy_improvement(self, ocr_simulator, random_coordinates):
        """Test that calibration significantly improves accuracy"""
        # Generate test data
        true_points = random_coordinates(n_points=100, seed=42)
        measured_points = ocr_simulator.measure_batch(true_points)

        # Errors before calibration
        errors_before = np.linalg.norm(measured_points - true_points, axis=1)
        mean_before = np.mean(errors_before)

        # Calibrate (use first 30 points)
        cal = SimpleCalibration()
        cal.calibrate(measured_points[:30], true_points[:30])

        # Errors after calibration
        corrected = cal.correct_batch(measured_points)
        errors_after = np.linalg.norm(corrected - true_points, axis=1)
        mean_after = np.mean(errors_after)

        # Should have significant improvement
        assert mean_after < mean_before
        assert mean_after < 1.0  # Should be sub-pixel

    def test_99_percent_accuracy(self, ocr_simulator, random_coordinates,
                                test_config):
        """Test achieving 99% accuracy (within 2px)"""
        # Generate large test set
        true_points = random_coordinates(n_points=500, seed=42)
        measured_points = ocr_simulator.measure_batch(true_points)

        # Calibrate with first 30 points
        cal = SimpleCalibration()
        cal.calibrate(measured_points[:30], true_points[:30])

        # Test on remaining points
        test_true = true_points[30:]
        test_measured = measured_points[30:]
        corrected = cal.correct_batch(test_measured)

        # Compute accuracy
        errors = np.linalg.norm(corrected - test_true, axis=1)
        success_rate = np.sum(errors <= test_config.accuracy_threshold) / len(errors)

        # Should achieve 99% accuracy
        assert success_rate >= 0.99

    def test_cross_validation(self, ocr_simulator, random_coordinates):
        """Test calibration with cross-validation"""
        # Generate data
        all_true = random_coordinates(n_points=100, seed=42)
        all_measured = ocr_simulator.measure_batch(all_true)

        # Split into train/test
        train_true = all_true[:50]
        train_measured = all_measured[:50]
        test_true = all_true[50:]
        test_measured = all_measured[50:]

        # Calibrate on training set
        cal = SimpleCalibration()
        cal.calibrate(train_measured, train_true)

        # Validate on test set
        corrected = cal.correct_batch(test_measured)
        errors = np.linalg.norm(corrected - test_true, axis=1)
        mean_error = np.mean(errors)

        # Should generalize well
        assert mean_error < 1.0

    @pytest.mark.performance
    def test_calibration_performance(self, random_coordinates, benchmark_timer):
        """Test calibration performance"""
        cal = SimpleCalibration()

        true_points = random_coordinates(n_points=1000)
        measured_points = true_points + np.array([3.5, -2.8])

        # Benchmark calibration
        _, time_cal = benchmark_timer.time_function(
            'calibrate',
            cal.calibrate,
            measured_points,
            true_points
        )

        # Should be fast (< 100ms for 1000 points)
        assert time_cal < 0.1

        # Benchmark batch correction
        test_points = random_coordinates(n_points=10000)
        _, time_correct = benchmark_timer.time_function(
            'correct_batch',
            cal.correct_batch,
            test_points
        )

        # Should be very fast (< 10ms for 10k points)
        assert time_correct < 0.01


# ============================================================================
# Integration Test
# ============================================================================

@pytest.mark.integration
class TestCalibrationIntegration:
    """Integration tests for calibration system"""

    def test_end_to_end_calibration_workflow(self, ocr_simulator,
                                             random_coordinates,
                                             temp_calibration_file,
                                             calculate_accuracy_metrics):
        """Test complete calibration workflow"""
        # Step 1: Generate calibration data
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)

        # Step 2: Calibrate
        cal = SimpleCalibration()
        cal.calibrate(calib_measured, calib_true)

        # Step 3: Save calibration
        cal.save(temp_calibration_file)

        # Step 4: Load in new session
        cal_loaded = SimpleCalibration()
        cal_loaded.load(temp_calibration_file)

        # Step 5: Test on new data
        test_true = random_coordinates(n_points=100, seed=99)
        test_measured = ocr_simulator.measure_batch(test_true)
        corrected = cal_loaded.correct_batch(test_measured)

        # Step 6: Validate accuracy
        metrics = calculate_accuracy_metrics(test_true, corrected)

        assert metrics['within_2px'] >= 0.99
        assert metrics['mean_error'] < 1.0
