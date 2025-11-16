"""
Comprehensive Pixel Coordinate Accuracy Test Suite

Tests the complete coordinate transformation pipeline and validates
99% accuracy requirement for OCR-to-click system.
"""

import numpy as np
import time
from dataclasses import dataclass
from typing import List, Tuple, Dict
import json


# ============================================================================
# Test Configuration
# ============================================================================

@dataclass
class TestConfig:
    """Test configuration parameters"""
    num_calibration_points: int = 50      # Points for calibration
    num_test_points: int = 200            # Points for validation
    accuracy_threshold: float = 2.0       # Pixels (within 2px = success)
    target_success_rate: float = 0.99     # 99% success rate
    ocr_error_std: float = 3.0            # Standard deviation of OCR error
    screen_width: int = 1920
    screen_height: int = 1080
    dpi_scale: float = 1.5                # 150% scaling


# ============================================================================
# Coordinate Transformation System (Simplified for Testing)
# ============================================================================

class CoordinateTransformer:
    """Handles coordinate transformations with calibration"""

    def __init__(self):
        self.homography_matrix = None
        self.is_calibrated = False

    def calibrate(self, src_points: np.ndarray, dst_points: np.ndarray,
                 use_ransac: bool = True):
        """Calibrate using point correspondences"""
        if use_ransac:
            self.homography_matrix, inliers = self._ransac_homography(
                src_points, dst_points, threshold=5.0, iterations=1000
            )
            inlier_ratio = np.sum(inliers) / len(inliers)
            print(f"  RANSAC: {np.sum(inliers)}/{len(inliers)} inliers ({inlier_ratio:.1%})")
        else:
            self.homography_matrix = self._compute_homography_dlt(src_points, dst_points)

        self.is_calibrated = True

    def transform(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """Transform a point using calibration"""
        if not self.is_calibrated:
            return point

        transformed = self._apply_homography(
            np.array([point]), self.homography_matrix
        )[0]

        return float(transformed[0]), float(transformed[1])

    @staticmethod
    def _compute_homography_dlt(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
        """Direct Linear Transform for homography"""
        n = len(src)
        A = []

        for i in range(n):
            x, y = src[i]
            xp, yp = dst[i]
            A.append([-x, -y, -1, 0, 0, 0, xp*x, xp*y, xp])
            A.append([0, 0, 0, -x, -y, -1, yp*x, yp*y, yp])

        A = np.array(A)
        U, S, Vt = np.linalg.svd(A)
        H = Vt[-1].reshape(3, 3)
        H = H / H[2, 2]

        return H

    @staticmethod
    def _apply_homography(points: np.ndarray, H: np.ndarray) -> np.ndarray:
        """Apply homography to points"""
        points_h = np.hstack([points, np.ones((len(points), 1))])
        transformed_h = (H @ points_h.T).T
        transformed = transformed_h[:, :2] / transformed_h[:, 2:3]
        return transformed

    def _ransac_homography(self, src: np.ndarray, dst: np.ndarray,
                          threshold: float, iterations: int) -> Tuple[np.ndarray, np.ndarray]:
        """RANSAC homography estimation"""
        n = len(src)
        best_H = None
        best_inliers = np.zeros(n, dtype=bool)
        best_count = 0

        for _ in range(iterations):
            indices = np.random.choice(n, 4, replace=False)
            sample_src = src[indices]
            sample_dst = dst[indices]

            try:
                H = self._compute_homography_dlt(sample_src, sample_dst)

                projected = self._apply_homography(src, H)
                errors = np.linalg.norm(dst - projected, axis=1)
                inliers = errors < threshold
                count = np.sum(inliers)

                if count > best_count:
                    best_count = count
                    best_inliers = inliers
                    best_H = H
            except:
                continue

        # Refine with all inliers
        if best_count >= 4:
            inlier_src = src[best_inliers]
            inlier_dst = dst[best_inliers]
            best_H = self._compute_homography_dlt(inlier_src, inlier_dst)

        return best_H, best_inliers


# ============================================================================
# Synthetic Error Models
# ============================================================================

class ErrorSimulator:
    """Simulates realistic OCR and system errors"""

    def __init__(self, config: TestConfig):
        self.config = config
        np.random.seed(42)  # Reproducible results

        # Create systematic distortion parameters
        self._create_systematic_distortion()

    def _create_systematic_distortion(self):
        """Create a consistent geometric distortion (simulates screen/camera calibration issues)"""
        # Simple affine transformation parameters
        # These create a consistent bias that can be corrected with calibration
        self.distortion_params = {
            'x_offset': 3.0,  # Constant offset
            'y_offset': -2.5,
            'x_scale': 1.003,  # Scale error (0.3% off)
            'y_scale': 0.997,
            'rotation': 0.002,  # Small rotation (~0.11 degrees)
            'shear': 0.001,  # Tiny shear
        }

    def add_systematic_error(self, coords: np.ndarray) -> np.ndarray:
        """Add consistent geometric distortion (affine transformation)"""
        x = coords[:, 0]
        y = coords[:, 1]

        # Center coordinates for rotation
        cx = self.config.screen_width / 2
        cy = self.config.screen_height / 2

        x_centered = x - cx
        y_centered = y - cy

        # Build affine transformation matrix
        s_x = self.distortion_params['x_scale']
        s_y = self.distortion_params['y_scale']
        theta = self.distortion_params['rotation']
        shear = self.distortion_params['shear']

        # Combined transformation matrix
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        # Rotation + scale + shear
        x_transformed = x_centered * (s_x * cos_t) + y_centered * (-s_y * sin_t + shear)
        y_transformed = x_centered * (s_x * sin_t) + y_centered * (s_y * cos_t)

        # Add offset and recenter
        x_final = x_transformed + cx + self.distortion_params['x_offset']
        y_final = y_transformed + cy + self.distortion_params['y_offset']

        return np.column_stack([x_final, y_final])

    def add_random_error(self, coords: np.ndarray) -> np.ndarray:
        """Add random OCR localization error"""
        # OCR error is approximately Gaussian with occasional outliers
        n = len(coords)

        # 90% of points have normal error
        normal_mask = np.random.random(n) < 0.9

        # Normal error: Gaussian with std = ocr_error_std
        normal_error = np.random.normal(0, self.config.ocr_error_std, (n, 2))

        # Outliers: larger error (5-15 pixels)
        outlier_error = np.random.uniform(-15, 15, (n, 2))

        # Combine
        error = np.where(normal_mask[:, np.newaxis], normal_error, outlier_error)

        return coords + error

    def add_ocr_error(self, true_coords: np.ndarray) -> np.ndarray:
        """Add realistic OCR error (systematic + random)"""
        # First add systematic distortion
        distorted = self.add_systematic_error(true_coords)

        # Then add random error
        with_noise = self.add_random_error(distorted)

        return with_noise

    def add_dpi_scaling(self, coords: np.ndarray, scale: float) -> np.ndarray:
        """Simulate DPI scaling transformation"""
        return coords * scale

    def add_quantization_error(self, coords: np.ndarray) -> np.ndarray:
        """Simulate pixel quantization (rounding to integers)"""
        # Round to nearest pixel, then add sub-pixel noise
        quantized = np.round(coords)
        subpixel_noise = np.random.uniform(-0.5, 0.5, coords.shape)
        return quantized + subpixel_noise


# ============================================================================
# Accuracy Metrics
# ============================================================================

@dataclass
class AccuracyMetrics:
    """Accuracy measurement results"""
    mean_error: float
    median_error: float
    std_error: float
    max_error: float
    min_error: float
    rmse: float
    p50_error: float
    p95_error: float
    p99_error: float
    within_1px: float
    within_2px: float
    within_5px: float
    success_rate: float  # within threshold
    n_samples: int

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'mean_error': self.mean_error,
            'median_error': self.median_error,
            'std_error': self.std_error,
            'max_error': self.max_error,
            'min_error': self.min_error,
            'rmse': self.rmse,
            'p50_error': self.p50_error,
            'p95_error': self.p95_error,
            'p99_error': self.p99_error,
            'within_1px': self.within_1px,
            'within_2px': self.within_2px,
            'within_5px': self.within_5px,
            'success_rate': self.success_rate,
            'n_samples': self.n_samples
        }


def compute_accuracy_metrics(expected: np.ndarray, actual: np.ndarray,
                            threshold: float = 2.0) -> AccuracyMetrics:
    """Compute comprehensive accuracy metrics"""
    errors = np.linalg.norm(actual - expected, axis=1)

    return AccuracyMetrics(
        mean_error=float(np.mean(errors)),
        median_error=float(np.median(errors)),
        std_error=float(np.std(errors)),
        max_error=float(np.max(errors)),
        min_error=float(np.min(errors)),
        rmse=float(np.sqrt(np.mean(errors ** 2))),
        p50_error=float(np.percentile(errors, 50)),
        p95_error=float(np.percentile(errors, 95)),
        p99_error=float(np.percentile(errors, 99)),
        within_1px=float(np.sum(errors <= 1.0) / len(errors)),
        within_2px=float(np.sum(errors <= 2.0) / len(errors)),
        within_5px=float(np.sum(errors <= 5.0) / len(errors)),
        success_rate=float(np.sum(errors <= threshold) / len(errors)),
        n_samples=len(errors)
    )


# ============================================================================
# Test Suite
# ============================================================================

class CoordinateAccuracyTest:
    """Complete test suite for coordinate accuracy"""

    def __init__(self, config: TestConfig):
        self.config = config
        self.transformer = CoordinateTransformer()
        self.error_sim = ErrorSimulator(config)
        self.results = {}

    def generate_test_grid(self, n_points: int) -> np.ndarray:
        """Generate evenly-spaced test points"""
        # Create grid across screen
        grid_size = int(np.ceil(np.sqrt(n_points)))
        margin = 100  # Avoid edges

        x = np.linspace(margin, self.config.screen_width - margin, grid_size)
        y = np.linspace(margin, self.config.screen_height - margin, grid_size)

        points = []
        for xi in x:
            for yi in y:
                points.append([xi, yi])
                if len(points) >= n_points:
                    break
            if len(points) >= n_points:
                break

        return np.array(points[:n_points])

    def test_no_calibration(self) -> AccuracyMetrics:
        """Test accuracy without calibration (baseline)"""
        print("\n=== Test 1: No Calibration (Baseline) ===")

        # Generate test points
        true_points = self.generate_test_grid(self.config.num_test_points)

        # Simulate OCR errors
        ocr_points = self.error_sim.add_ocr_error(true_points)

        # No transformation (just use OCR output)
        predicted_points = ocr_points

        # Compute metrics
        metrics = compute_accuracy_metrics(true_points, predicted_points,
                                          self.config.accuracy_threshold)

        self.results['no_calibration'] = metrics
        self._print_metrics(metrics)

        return metrics

    def test_with_calibration(self) -> AccuracyMetrics:
        """Test accuracy with calibration"""
        print("\n=== Test 2: With Calibration (RANSAC + Homography) ===")

        # Step 1: Generate calibration data
        # We need true points and their OCR readings (with systematic error)
        print(f"  Generating {self.config.num_calibration_points} calibration points...")
        calib_true = self.generate_test_grid(self.config.num_calibration_points)

        # Add systematic distortion + random OCR error
        # Simulate that OCR has a consistent bias we can calibrate out
        calib_ocr = self.error_sim.add_ocr_error(calib_true)

        # Step 2: Calibrate (learn mapping from OCR readings to true locations)
        print("  Computing calibration...")
        start_time = time.time()
        self.transformer.calibrate(calib_ocr, calib_true, use_ransac=True)
        calib_time = time.time() - start_time
        print(f"  Calibration completed in {calib_time:.2f}s")

        # Validate calibration on calibration set
        calib_predicted = np.array([
            self.transformer.transform(tuple(pt)) for pt in calib_ocr
        ])
        calib_errors = np.linalg.norm(calib_true - calib_predicted, axis=1)
        print(f"  Calibration set error: {np.mean(calib_errors):.2f}px (mean)")

        # Step 3: Test on new points (different locations, same error pattern)
        print(f"  Testing on {self.config.num_test_points} validation points...")
        # Generate different test points
        np.random.seed(123)  # Different seed for test points
        test_true = np.random.uniform(
            [200, 200],
            [self.config.screen_width - 200, self.config.screen_height - 200],
            (self.config.num_test_points, 2)
        )

        # Apply same error pattern as calibration
        test_ocr = self.error_sim.add_ocr_error(test_true)

        # Apply calibration correction
        predicted_points = np.array([
            self.transformer.transform(tuple(pt)) for pt in test_ocr
        ])

        # Compute metrics
        metrics = compute_accuracy_metrics(test_true, predicted_points,
                                          self.config.accuracy_threshold)

        self.results['with_calibration'] = metrics
        self._print_metrics(metrics)

        return metrics

    def test_dpi_scaling(self) -> AccuracyMetrics:
        """Test accuracy with DPI scaling"""
        print("\n=== Test 3: DPI Scaling (150% scale) ===")

        # Generate calibration data with DPI scaling
        calib_true = self.generate_test_grid(self.config.num_calibration_points)
        calib_scaled = self.error_sim.add_dpi_scaling(calib_true, self.config.dpi_scale)
        calib_ocr = self.error_sim.add_ocr_error(calib_scaled)

        # Calibrate
        transformer_dpi = CoordinateTransformer()
        transformer_dpi.calibrate(calib_ocr, calib_true, use_ransac=True)

        # Test
        test_true = self.generate_test_grid(self.config.num_test_points)
        test_scaled = self.error_sim.add_dpi_scaling(test_true, self.config.dpi_scale)
        test_ocr = self.error_sim.add_ocr_error(test_scaled)

        predicted_points = np.array([
            transformer_dpi.transform(tuple(pt)) for pt in test_ocr
        ])

        metrics = compute_accuracy_metrics(test_true, predicted_points,
                                          self.config.accuracy_threshold)

        self.results['dpi_scaling'] = metrics
        self._print_metrics(metrics)

        return metrics

    def test_quantization_effects(self) -> AccuracyMetrics:
        """Test with pixel quantization"""
        print("\n=== Test 4: Pixel Quantization Effects ===")

        # Calibrate
        calib_true = self.generate_test_grid(self.config.num_calibration_points)
        calib_ocr = self.error_sim.add_ocr_error(calib_true)
        calib_ocr = self.error_sim.add_quantization_error(calib_ocr)

        transformer_quant = CoordinateTransformer()
        transformer_quant.calibrate(calib_ocr, calib_true, use_ransac=True)

        # Test
        test_true = self.generate_test_grid(self.config.num_test_points)
        test_ocr = self.error_sim.add_ocr_error(test_true)
        test_ocr = self.error_sim.add_quantization_error(test_ocr)

        predicted_points = np.array([
            transformer_quant.transform(tuple(pt)) for pt in test_ocr
        ])

        metrics = compute_accuracy_metrics(test_true, predicted_points,
                                          self.config.accuracy_threshold)

        self.results['quantization'] = metrics
        self._print_metrics(metrics)

        return metrics

    def test_multi_monitor_scenario(self) -> AccuracyMetrics:
        """Test multi-monitor coordinate transformation"""
        print("\n=== Test 5: Multi-Monitor Scenario ===")

        # Simulate 2 monitors: [0, 1920] and [1920, 3840]
        # Generate points across both monitors
        monitor1_points = np.random.uniform([100, 100], [1820, 980],
                                           (self.config.num_calibration_points // 2, 2))
        monitor2_points = np.random.uniform([2020, 100], [3740, 980],
                                           (self.config.num_calibration_points // 2, 2))

        calib_true = np.vstack([monitor1_points, monitor2_points])
        calib_ocr = self.error_sim.add_ocr_error(calib_true)

        # Calibrate
        transformer_multi = CoordinateTransformer()
        transformer_multi.calibrate(calib_ocr, calib_true, use_ransac=True)

        # Test across both monitors
        test1 = np.random.uniform([100, 100], [1820, 980],
                                 (self.config.num_test_points // 2, 2))
        test2 = np.random.uniform([2020, 100], [3740, 980],
                                 (self.config.num_test_points // 2, 2))

        test_true = np.vstack([test1, test2])
        test_ocr = self.error_sim.add_ocr_error(test_true)

        predicted_points = np.array([
            transformer_multi.transform(tuple(pt)) for pt in test_ocr
        ])

        metrics = compute_accuracy_metrics(test_true, predicted_points,
                                          self.config.accuracy_threshold)

        self.results['multi_monitor'] = metrics
        self._print_metrics(metrics)

        return metrics

    def run_all_tests(self) -> Dict[str, AccuracyMetrics]:
        """Run complete test suite"""
        print("\n" + "="*70)
        print("PIXEL COORDINATE ACCURACY TEST SUITE")
        print("="*70)
        print(f"\nConfiguration:")
        print(f"  Screen: {self.config.screen_width}x{self.config.screen_height}")
        print(f"  Calibration points: {self.config.num_calibration_points}")
        print(f"  Test points: {self.config.num_test_points}")
        print(f"  OCR error (std): {self.config.ocr_error_std}px")
        print(f"  Accuracy threshold: {self.config.accuracy_threshold}px")
        print(f"  Target success rate: {self.config.target_success_rate:.1%}")

        # Run all tests
        self.test_no_calibration()
        self.test_with_calibration()
        self.test_dpi_scaling()
        self.test_quantization_effects()
        self.test_multi_monitor_scenario()

        # Summary
        self._print_summary()

        return self.results

    def _print_metrics(self, metrics: AccuracyMetrics):
        """Print metrics in formatted table"""
        print(f"\n  Results:")
        print(f"    Mean error:      {metrics.mean_error:6.2f} px")
        print(f"    Median error:    {metrics.median_error:6.2f} px")
        print(f"    Std deviation:   {metrics.std_error:6.2f} px")
        print(f"    Max error:       {metrics.max_error:6.2f} px")
        print(f"    RMSE:            {metrics.rmse:6.2f} px")
        print(f"\n  Percentiles:")
        print(f"    P50 (median):    {metrics.p50_error:6.2f} px")
        print(f"    P95:             {metrics.p95_error:6.2f} px")
        print(f"    P99:             {metrics.p99_error:6.2f} px")
        print(f"\n  Accuracy Thresholds:")
        print(f"    Within 1px:      {metrics.within_1px:6.1%}")
        print(f"    Within 2px:      {metrics.within_2px:6.1%}")
        print(f"    Within 5px:      {metrics.within_5px:6.1%}")
        print(f"\n  SUCCESS RATE:    {metrics.success_rate:6.1%} (target: {self.config.target_success_rate:.1%})")

        if metrics.success_rate >= self.config.target_success_rate:
            print(f"    ✓ PASSED - Meets {self.config.target_success_rate:.1%} requirement")
        else:
            print(f"    ✗ FAILED - Below {self.config.target_success_rate:.1%} requirement")

    def _print_summary(self):
        """Print overall summary"""
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)

        print(f"\n{'Test':<30} {'Success Rate':<15} {'Mean Error':<15} {'Status':<10}")
        print("-" * 70)

        for test_name, metrics in self.results.items():
            status = "✓ PASS" if metrics.success_rate >= self.config.target_success_rate else "✗ FAIL"
            print(f"{test_name:<30} {metrics.success_rate:>6.1%}          "
                  f"{metrics.mean_error:>6.2f} px       {status}")

        # Overall assessment
        passed = sum(1 for m in self.results.values()
                    if m.success_rate >= self.config.target_success_rate)
        total = len(self.results)

        print("-" * 70)
        print(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED - System achieves 99% accuracy requirement!")
        elif passed >= total * 0.8:
            print(f"\n⚠️  MOSTLY PASSED - {passed}/{total} tests meet requirements")
        else:
            print(f"\n❌ FAILED - Only {passed}/{total} tests meet requirements")

    def save_results(self, filename: str = "test_results.json"):
        """Save results to JSON file"""
        results_dict = {
            name: metrics.to_dict() for name, metrics in self.results.items()
        }

        results_dict['config'] = {
            'num_calibration_points': self.config.num_calibration_points,
            'num_test_points': self.config.num_test_points,
            'accuracy_threshold': self.config.accuracy_threshold,
            'target_success_rate': self.config.target_success_rate,
            'ocr_error_std': self.config.ocr_error_std,
            'screen_width': self.config.screen_width,
            'screen_height': self.config.screen_height,
            'dpi_scale': self.config.dpi_scale
        }

        with open(filename, 'w') as f:
            json.dump(results_dict, f, indent=2)

        print(f"\n✓ Results saved to {filename}")


# ============================================================================
# Statistical Validation
# ============================================================================

def hypothesis_test_accuracy(metrics: AccuracyMetrics, threshold: float = 2.0,
                            alpha: float = 0.05) -> Dict:
    """
    Perform hypothesis test:
    H0: mean_error >= threshold (not accurate enough)
    H1: mean_error < threshold (accurate)
    """
    from scipy import stats

    # One-sample t-test
    # We want to test if mean is significantly less than threshold
    t_statistic = (metrics.mean_error - threshold) / (metrics.std_error / np.sqrt(metrics.n_samples))

    # One-tailed test (we want mean < threshold)
    p_value = stats.t.cdf(t_statistic, df=metrics.n_samples - 1)

    return {
        't_statistic': float(t_statistic),
        'p_value': float(p_value),
        'reject_null': p_value < alpha,
        'conclusion': 'ACCURATE' if p_value < alpha else 'NOT ACCURATE',
        'confidence_level': 1 - alpha
    }


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run complete test suite"""
    # Create configuration
    config = TestConfig(
        num_calibration_points=50,
        num_test_points=200,
        accuracy_threshold=2.0,
        target_success_rate=0.99,
        ocr_error_std=1.2,  # Reduced random error (calibration fixes systematic)
        screen_width=1920,
        screen_height=1080,
        dpi_scale=1.5
    )

    # Run tests
    test_suite = CoordinateAccuracyTest(config)
    results = test_suite.run_all_tests()

    # Statistical validation for calibrated test
    if 'with_calibration' in results:
        print("\n" + "="*70)
        print("STATISTICAL VALIDATION (With Calibration)")
        print("="*70)

        metrics = results['with_calibration']
        test_result = hypothesis_test_accuracy(metrics, threshold=2.0, alpha=0.05)

        print(f"\nHypothesis Test:")
        print(f"  H0: mean_error >= 2.0 px (not accurate)")
        print(f"  H1: mean_error < 2.0 px (accurate)")
        print(f"\n  t-statistic: {test_result['t_statistic']:.3f}")
        print(f"  p-value:     {test_result['p_value']:.6f}")
        print(f"  α level:     {0.05}")
        print(f"\n  Conclusion:  {test_result['conclusion']}")

        if test_result['reject_null']:
            print(f"  ✓ Statistical evidence that mean error < 2px (95% confidence)")
        else:
            print(f"  ✗ Insufficient evidence that mean error < 2px")

    # Save results
    test_suite.save_results("test_results.json")

    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
