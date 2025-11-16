"""
Integration Tests for Complete MCP Server System
End-to-end tests: OCR → Calibration → Transform → Click

Reuses logic from:
- test_ultra_accuracy.py (100% accuracy validation)
- test_simple_accuracy.py (99% accuracy with calibration)
- test_real_window_clicking.py (dynamic window scenarios)
"""

import pytest
import numpy as np
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from scipy import stats


# ============================================================================
# Import Components from Other Test Files
# ============================================================================

# These would normally be imported from the actual implementation
# For testing, we'll reference the implementations from other test files


@dataclass
class IntegrationTestConfig:
    """Configuration for integration tests"""
    screen_width: int = 1920
    screen_height: int = 1080
    dpi_scale: float = 1.0

    # OCR parameters
    ocr_systematic_bias: Tuple[float, float] = (3.5, -2.8)
    ocr_random_error_std: float = 0.55

    # Calibration parameters
    calibration_points: int = 30
    regional_grid: Tuple[int, int] = (2, 2)

    # Accuracy targets
    accuracy_threshold: float = 2.0
    target_success_rate: float = 0.99


# ============================================================================
# Test Class: End-to-End Pipeline
# ============================================================================

@pytest.mark.integration
class TestEndToEndPipeline:
    """Test complete pipeline from OCR to click execution"""

    def test_simple_end_to_end(self, ocr_simulator, mock_calibration,
                               mock_coordinate_transformer, mock_click_executor,
                               random_coordinates):
        """Test basic end-to-end workflow"""
        # Step 1: Generate calibration data
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)

        # Step 2: Calibrate
        mock_calibration.calibrate(calib_measured, calib_true)

        # Step 3: Test on new data
        test_true = random_coordinates(n_points=10, seed=99)
        test_measured = ocr_simulator.measure_batch(test_true)

        # Step 4: Transform coordinates
        for measured in test_measured:
            corrected = mock_calibration.correct(measured)

            # Step 5: Execute click
            event = mock_click_executor.click(corrected[0], corrected[1])

            assert event.success is True

        # Verify all clicks executed
        assert mock_click_executor.get_click_count() == 10

    def test_ocr_to_click_with_accuracy_validation(self, ocr_simulator,
                                                   mock_calibration,
                                                   mock_click_executor,
                                                   random_coordinates,
                                                   calculate_accuracy_metrics):
        """Test end-to-end with accuracy validation (99% target)"""
        config = IntegrationTestConfig()

        # Calibration phase
        calib_true = random_coordinates(n_points=config.calibration_points, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Test phase
        test_true = random_coordinates(n_points=500, seed=99)
        test_measured = ocr_simulator.measure_batch(test_true)

        # Apply calibration and click
        clicked_coords = []
        for measured in test_measured:
            corrected = mock_calibration.correct(measured)
            event = mock_click_executor.click(corrected[0], corrected[1])
            clicked_coords.append([event.x, event.y])

        # Validate accuracy
        metrics = calculate_accuracy_metrics(test_true, np.array(clicked_coords))

        assert metrics['within_2px'] >= config.target_success_rate
        assert metrics['mean_error'] < 1.0

    def test_multi_pass_ocr_integration(self, ocr_simulator, mock_calibration,
                                       mock_click_executor, random_coordinates,
                                       calculate_accuracy_metrics):
        """Test with multi-pass OCR averaging"""
        # Calibration
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Test with multi-pass OCR
        test_true = random_coordinates(n_points=100, seed=99)

        clicked_coords = []
        for true_coord in test_true:
            # Multi-pass measurement (reduces random error)
            measured = ocr_simulator.multi_pass_measure(true_coord, num_passes=3)

            # Apply calibration
            corrected = mock_calibration.correct(measured)

            # Click
            event = mock_click_executor.click(corrected[0], corrected[1])
            clicked_coords.append([event.x, event.y])

        # Should have better accuracy than single-pass
        metrics = calculate_accuracy_metrics(test_true, np.array(clicked_coords))

        assert metrics['within_2px'] >= 0.99
        assert metrics['within_1px'] >= 0.90  # Very high precision


# ============================================================================
# Test Class: Synthetic Data Tests (from test_ultra_accuracy.py)
# ============================================================================

@pytest.mark.integration
class TestSyntheticDataAccuracy:
    """Test accuracy on synthetic data with known ground truth"""

    def test_ultra_accuracy_100_calibration_points(self, ocr_simulator,
                                                    random_coordinates):
        """Test with 100 calibration points (ultra accuracy approach)"""
        from test_calibration import RegionalCalibration

        config = IntegrationTestConfig(calibration_points=100)

        # Create regional calibration system
        regional_cal = RegionalCalibration(
            grid_size=config.regional_grid,
            screen_size=(config.screen_width, config.screen_height)
        )

        # Generate calibration points distributed across regions
        calib_true = random_coordinates(n_points=100, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)

        # Calibrate
        regional_cal.calibrate(calib_measured, calib_true)

        # Test on large dataset
        test_true = random_coordinates(n_points=1000, seed=99)
        test_measured = ocr_simulator.measure_batch(test_true)

        # Correct with regional calibration
        corrected = regional_cal.correct_batch(test_measured)

        # Compute errors
        errors = np.linalg.norm(corrected - test_true, axis=1)
        success_rate = np.sum(errors <= 2.0) / len(errors)

        # Should achieve very high accuracy
        assert success_rate >= 0.995  # 99.5% or better

    def test_regional_vs_simple_calibration_comparison(self, ocr_simulator,
                                                       grid_coordinates):
        """Compare regional vs simple calibration accuracy"""
        from test_calibration import SimpleCalibration, RegionalCalibration

        # Generate spatially-varying error pattern
        np.random.seed(42)

        # Create test points across screen
        test_true = grid_coordinates(grid_size=(20, 15), margin=100)

        # Simulate spatially-varying measurement error
        test_measured = []
        for pt in test_true:
            x, y = pt

            # Error varies by screen region
            if x < 960:  # Left half
                bias = np.array([2.0, -1.0])
            else:  # Right half
                bias = np.array([5.0, -4.0])

            # Add bias + random noise
            measured = pt + bias + np.random.normal(0, 0.5, 2)
            test_measured.append(measured)

        test_measured = np.array(test_measured)

        # Split into calibration and test sets
        calib_true = test_true[:50]
        calib_measured = test_measured[:50]
        eval_true = test_true[50:]
        eval_measured = test_measured[50:]

        # Simple calibration
        simple_cal = SimpleCalibration()
        simple_cal.calibrate(calib_measured, calib_true)
        simple_corrected = simple_cal.correct_batch(eval_measured)
        simple_errors = np.linalg.norm(simple_corrected - eval_true, axis=1)
        simple_mean = np.mean(simple_errors)

        # Regional calibration
        regional_cal = RegionalCalibration((2, 2), (1920, 1080))
        regional_cal.calibrate(calib_measured, calib_true)
        regional_corrected = regional_cal.correct_batch(eval_measured)
        regional_errors = np.linalg.norm(regional_corrected - eval_true, axis=1)
        regional_mean = np.mean(regional_errors)

        # Regional should be significantly better for spatially-varying errors
        assert regional_mean < simple_mean
        assert regional_mean < 1.0

    def test_5000_point_ultra_accuracy(self, ocr_simulator, random_coordinates):
        """Test ultra-high accuracy on 5000 points (like test_ultra_accuracy.py)"""
        from test_calibration import RegionalCalibration

        # Calibrate with 100 points
        calib_true = random_coordinates(n_points=100, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)

        regional_cal = RegionalCalibration((2, 2), (1920, 1080))
        regional_cal.calibrate(calib_measured, calib_true)

        # Test on 5000 points
        np.random.seed(999)
        test_true = random_coordinates(n_points=5000, seed=999)

        # Multi-pass OCR for each point (reduces variance)
        test_corrected = []
        for pt in test_true:
            measured = ocr_simulator.multi_pass_measure(pt, num_passes=3)
            corrected = regional_cal.correct(measured)
            test_corrected.append(corrected)

        test_corrected = np.array(test_corrected)

        # Compute accuracy
        errors = np.linalg.norm(test_true - test_corrected, axis=1)
        within_2px = np.sum(errors <= 2.0) / len(errors)

        # Should achieve near-100% accuracy
        assert within_2px >= 0.998  # 99.8% or better


# ============================================================================
# Test Class: Real-World Window Clicking Scenarios
# ============================================================================

@pytest.mark.integration
class TestWindowClickingScenarios:
    """Test clicking scenarios from test_real_window_clicking.py"""

    @pytest.fixture
    def desktop_windows(self, mock_windows):
        """Create realistic window layout"""
        return mock_windows

    def test_clicking_across_different_window_sizes(self, ocr_simulator,
                                                    mock_calibration,
                                                    mock_click_executor,
                                                    desktop_windows,
                                                    random_coordinates):
        """Test clicking UI elements in windows of different sizes"""
        # Calibrate
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Generate click targets in each window
        click_results = []

        for window in desktop_windows:
            # Generate 5 click targets per window
            for _ in range(5):
                # Random position within window
                x = np.random.uniform(window.x + 50, window.x + window.width - 50)
                y = np.random.uniform(window.y + 50, window.y + window.height - 50)

                true_coord = np.array([x, y])

                # Simulate OCR measurement
                measured = ocr_simulator.measure(true_coord)

                # Apply calibration
                corrected = mock_calibration.correct(measured)

                # Click
                event = mock_click_executor.click(corrected[0], corrected[1])

                # Verify click is in correct window
                click_in_window = window.contains_point(event.x, event.y)

                click_results.append({
                    'window': window.title,
                    'window_size': (window.width, window.height),
                    'click_in_window': click_in_window,
                    'error': np.linalg.norm([event.x - x, event.y - y])
                })

        # All clicks should be in correct windows
        success_rate = sum(1 for r in click_results if r['click_in_window']) / len(click_results)
        mean_error = np.mean([r['error'] for r in click_results])

        assert success_rate >= 0.95  # 95% clicks in correct window
        assert mean_error < 2.0  # Mean error < 2 pixels

    def test_clicking_at_window_edges(self, ocr_simulator, mock_calibration,
                                     mock_click_executor, mock_windows):
        """Test clicking near window edges (title bar, borders)"""
        # Calibrate
        np.random.seed(42)
        calib_true = np.random.uniform([100, 100], [1800, 980], (30, 2))
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        for window in mock_windows:
            # Test clicking near edges
            edge_targets = [
                (window.x + 20, window.y + 10),  # Near top-left
                (window.x + window.width - 30, window.y + 10),  # Close button area
                (window.x + window.width // 2, window.y + 20),  # Title bar center
                (window.x + 20, window.y + window.height - 40),  # Bottom-left
                (window.x + window.width - 100, window.y + window.height - 40),  # OK button area
            ]

            for target_x, target_y in edge_targets:
                measured = ocr_simulator.measure(np.array([target_x, target_y]))
                corrected = mock_calibration.correct(measured)
                event = mock_click_executor.click(corrected[0], corrected[1])

                # Should still click within window
                assert window.contains_point(event.x, event.y)

    def test_dynamic_window_movement(self, ocr_simulator, mock_calibration,
                                    mock_click_executor):
        """Test clicking when window positions change"""
        from dataclasses import dataclass

        @dataclass
        class MovableWindow:
            x: int
            y: int
            width: int
            height: int

            def move(self, dx, dy):
                self.x += dx
                self.y += dy

            def contains_point(self, px, py):
                return (self.x <= px <= self.x + self.width and
                       self.y <= py <= self.y + self.height)

        # Create movable window
        window = MovableWindow(x=100, y=100, width=800, height=600)

        # Calibrate once
        np.random.seed(42)
        calib_true = np.random.uniform([150, 150], [1750, 930], (30, 2))
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Test clicking as window moves
        positions = [
            (100, 100),   # Initial
            (300, 200),   # Moved
            (500, 300),   # Moved again
            (700, 100),   # Near right edge
        ]

        for pos_x, pos_y in positions:
            window.x = pos_x
            window.y = pos_y

            # Click center of window
            target_x = window.x + window.width // 2
            target_y = window.y + window.height // 2

            measured = ocr_simulator.measure(np.array([target_x, target_y]))
            corrected = mock_calibration.correct(measured)
            event = mock_click_executor.click(corrected[0], corrected[1])

            # Click should be in window at new position
            assert window.contains_point(event.x, event.y)


# ============================================================================
# Test Class: Statistical Validation
# ============================================================================

@pytest.mark.integration
class TestStatisticalValidation:
    """Statistical validation of accuracy (from test_simple_accuracy.py)"""

    def test_hypothesis_test_for_accuracy(self, ocr_simulator, mock_calibration,
                                         random_coordinates):
        """Test hypothesis: mean error < 2px"""
        # Calibrate
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Large test set for statistical power
        test_true = random_coordinates(n_points=500, seed=99)
        test_measured = ocr_simulator.measure_batch(test_true)
        corrected = mock_calibration.correct_batch(test_measured)

        # Compute errors
        errors = np.linalg.norm(corrected - test_true, axis=1)
        mean_error = np.mean(errors)
        std_error = np.std(errors, ddof=1)
        n = len(errors)

        # Hypothesis test: H0: mean >= 2px, H1: mean < 2px
        accuracy_threshold = 2.0
        t_stat = (mean_error - accuracy_threshold) / (std_error / np.sqrt(n))
        p_value = stats.t.cdf(t_stat, df=n-1)

        # Should reject H0 (mean error is significantly < 2px)
        assert p_value < 0.05

    def test_confidence_interval_for_mean_error(self, ocr_simulator,
                                               mock_calibration,
                                               random_coordinates):
        """Test 95% confidence interval for mean error"""
        # Calibrate
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Test
        test_true = random_coordinates(n_points=500, seed=99)
        test_measured = ocr_simulator.measure_batch(test_true)
        corrected = mock_calibration.correct_batch(test_measured)

        # Compute CI
        errors = np.linalg.norm(corrected - test_true, axis=1)
        mean_error = np.mean(errors)
        std_error = np.std(errors, ddof=1)
        n = len(errors)

        ci_margin = stats.t.ppf(0.975, df=n-1) * (std_error / np.sqrt(n))
        ci_lower = mean_error - ci_margin
        ci_upper = mean_error + ci_margin

        # Upper bound of CI should be < 2px
        assert ci_upper < 2.0

    def test_accuracy_breakdown_by_percentile(self, ocr_simulator,
                                              mock_calibration,
                                              random_coordinates):
        """Test accuracy at different percentiles"""
        # Calibrate
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Test
        test_true = random_coordinates(n_points=1000, seed=99)
        test_measured = ocr_simulator.measure_batch(test_true)
        corrected = mock_calibration.correct_batch(test_measured)

        # Compute errors
        errors = np.linalg.norm(corrected - test_true, axis=1)

        # Check percentiles
        p50 = np.percentile(errors, 50)  # Median
        p90 = np.percentile(errors, 90)
        p95 = np.percentile(errors, 95)
        p99 = np.percentile(errors, 99)

        # Validate accuracy distribution
        assert p50 < 1.0   # Median error < 1px
        assert p90 < 1.5   # 90th percentile < 1.5px
        assert p95 < 2.0   # 95th percentile < 2px
        assert p99 < 3.0   # 99th percentile < 3px


# ============================================================================
# Test Class: Performance Benchmarks
# ============================================================================

@pytest.mark.performance
@pytest.mark.integration
class TestPerformanceBenchmarks:
    """Performance benchmarks for complete pipeline"""

    def test_end_to_end_latency(self, ocr_simulator, mock_calibration,
                               mock_click_executor, random_coordinates,
                               benchmark_timer):
        """Test end-to-end latency for single click"""
        # Setup
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        def single_click_workflow(coord):
            measured = ocr_simulator.measure(coord)
            corrected = mock_calibration.correct(measured)
            event = mock_click_executor.click(corrected[0], corrected[1])
            return event

        # Benchmark single click
        test_coord = np.array([500, 400])
        _, latency = benchmark_timer.time_function(
            'single_click',
            single_click_workflow,
            test_coord
        )

        # Should be fast (< 1ms for mock implementation)
        assert latency < 0.001

    def test_throughput_100_clicks(self, ocr_simulator, mock_calibration,
                                   mock_click_executor, random_coordinates,
                                   benchmark_timer):
        """Test throughput for 100 clicks"""
        # Setup
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        test_coords = random_coordinates(n_points=100, seed=99)

        def batch_click_workflow():
            for coord in test_coords:
                measured = ocr_simulator.measure(coord)
                corrected = mock_calibration.correct(measured)
                mock_click_executor.click(corrected[0], corrected[1])

        # Benchmark batch
        _, elapsed = benchmark_timer.time_function(
            'batch_100_clicks',
            batch_click_workflow
        )

        # Should process quickly
        assert elapsed < 0.01  # < 10ms for 100 clicks
        clicks_per_second = 100 / elapsed
        assert clicks_per_second > 10000  # > 10k clicks/sec


# ============================================================================
# Test Class: Error Cases and Edge Cases
# ============================================================================

@pytest.mark.integration
class TestErrorCases:
    """Test error handling and edge cases"""

    def test_insufficient_calibration_points(self, ocr_simulator, mock_calibration):
        """Test behavior with too few calibration points"""
        # Only 2 points - should fail
        calib_true = np.array([[100, 100], [200, 200]])
        calib_measured = ocr_simulator.measure_batch(calib_true)

        with pytest.raises(ValueError, match="at least 3"):
            mock_calibration.calibrate(calib_measured, calib_true)

    def test_out_of_bounds_clicks(self, ocr_simulator, mock_calibration,
                                  mock_click_executor):
        """Test clicking coordinates outside screen bounds"""
        from test_click_executor import ClickExecutor

        # Setup
        calib_true = np.random.uniform([100, 100], [1800, 980], (30, 2))
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Create executor with validation
        executor = ClickExecutor(1920, 1080, validate_coords=True, safety_margin=10)

        # Try clicking near edge (should fail without auto_clamp)
        with pytest.raises(ValueError):
            executor.click(5, 500)

        # With auto_clamp should succeed
        event = executor.click(5, 500, auto_clamp=True)
        assert event.success is True
        assert event.x >= 10  # Clamped to margin

    def test_uncalibrated_system_behavior(self, ocr_simulator, mock_click_executor,
                                         random_coordinates):
        """Test system behavior without calibration"""
        from test_calibration import SimpleCalibration

        cal = SimpleCalibration()

        # Try to correct without calibration
        test_coord = np.array([500, 400])
        corrected = cal.correct(test_coord)

        # Should return unchanged
        np.testing.assert_array_equal(corrected, test_coord)


# ============================================================================
# Test Class: Result Reporting
# ============================================================================

@pytest.mark.integration
class TestResultReporting:
    """Test result collection and reporting (like test files)"""

    def test_generate_accuracy_report(self, ocr_simulator, mock_calibration,
                                     random_coordinates, test_results_dir,
                                     calculate_accuracy_metrics):
        """Generate comprehensive accuracy report"""
        # Calibrate
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Test
        test_true = random_coordinates(n_points=500, seed=99)
        test_measured = ocr_simulator.measure_batch(test_true)
        corrected = mock_calibration.correct_batch(test_measured)

        # Calculate metrics
        metrics = calculate_accuracy_metrics(test_true, corrected)

        # Generate report
        report = {
            'test_type': 'integration_accuracy',
            'calibration': {
                'num_points': 30,
                'method': 'simple_offset'
            },
            'test_set_size': 500,
            'metrics': metrics,
            'success': metrics['within_2px'] >= 0.99
        }

        # Save report
        report_file = test_results_dir / 'integration_accuracy_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        assert report_file.exists()
        assert report['success'] is True

    def test_benchmark_results_export(self, ocr_simulator, mock_calibration,
                                     mock_click_executor, random_coordinates,
                                     test_results_dir, benchmark_timer):
        """Export performance benchmark results"""
        # Setup
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Run benchmarks
        test_coords = random_coordinates(n_points=100, seed=99)

        for coord in test_coords:
            def workflow():
                measured = ocr_simulator.measure(coord)
                corrected = mock_calibration.correct(measured)
                return mock_click_executor.click(corrected[0], corrected[1])

            benchmark_timer.time_function('click_workflow', workflow)

        # Get stats
        stats = benchmark_timer.get_stats('click_workflow')

        # Export
        results = {
            'benchmark': 'click_workflow',
            'num_iterations': stats['count'],
            'mean_ms': stats['mean'] * 1000,
            'median_ms': stats['median'] * 1000,
            'std_ms': stats['std'] * 1000,
            'min_ms': stats['min'] * 1000,
            'max_ms': stats['max'] * 1000
        }

        results_file = test_results_dir / 'benchmark_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        assert results_file.exists()
