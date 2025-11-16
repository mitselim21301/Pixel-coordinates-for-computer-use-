"""
Tests for Click Execution System
Tests click execution (mocked), button types, coordinate validation.
"""

import pytest
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from unittest.mock import Mock, MagicMock, patch


# ============================================================================
# Click Executor System
# ============================================================================

class MouseButton(Enum):
    """Mouse button types"""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


@dataclass
class ClickEvent:
    """Record of a click event"""
    x: float
    y: float
    button: MouseButton
    double: bool = False
    timestamp: Optional[float] = None
    success: bool = True


class CoordinateValidator:
    """Validate coordinates before clicking"""

    def __init__(self, screen_width=1920, screen_height=1080, margin=0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.margin = margin

    def is_valid(self, x: float, y: float) -> bool:
        """Check if coordinates are within valid screen bounds"""
        return (self.margin <= x <= self.screen_width - self.margin and
                self.margin <= y <= self.screen_height - self.margin)

    def validate(self, x: float, y: float) -> Tuple[bool, str]:
        """
        Validate coordinates with detailed error message

        Returns:
            (is_valid, error_message)
        """
        if x < self.margin:
            return False, f"X coordinate {x} too close to left edge (margin: {self.margin})"
        if x > self.screen_width - self.margin:
            return False, f"X coordinate {x} too close to right edge (max: {self.screen_width - self.margin})"
        if y < self.margin:
            return False, f"Y coordinate {y} too close to top edge (margin: {self.margin})"
        if y > self.screen_height - self.margin:
            return False, f"Y coordinate {y} too close to bottom edge (max: {self.screen_height - self.margin})"

        return True, ""

    def clamp(self, x: float, y: float) -> Tuple[float, float]:
        """Clamp coordinates to valid range"""
        x_clamped = max(self.margin, min(self.screen_width - self.margin, x))
        y_clamped = max(self.margin, min(self.screen_height - self.margin, y))
        return (x_clamped, y_clamped)


class ClickExecutor:
    """Execute mouse clicks with validation and error handling"""

    def __init__(self, screen_width=1920, screen_height=1080,
                 validate_coords=True, safety_margin=0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.validate_coords = validate_coords
        self.safety_margin = safety_margin

        self.validator = CoordinateValidator(
            screen_width, screen_height, safety_margin
        )

        # Click history for testing
        self.click_history = []
        self.last_click = None

    def click(self, x: float, y: float,
             button: MouseButton = MouseButton.LEFT,
             double: bool = False,
             auto_clamp: bool = False) -> ClickEvent:
        """
        Execute a mouse click

        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button to click
            double: Whether to double-click
            auto_clamp: Whether to automatically clamp out-of-bounds coordinates

        Returns:
            ClickEvent with execution details

        Raises:
            ValueError: If coordinates are invalid and auto_clamp is False
        """
        import time

        # Validate coordinates
        if self.validate_coords:
            is_valid, error_msg = self.validator.validate(x, y)

            if not is_valid:
                if auto_clamp:
                    x, y = self.validator.clamp(x, y)
                else:
                    raise ValueError(f"Invalid coordinates: {error_msg}")

        # Create click event
        event = ClickEvent(
            x=x,
            y=y,
            button=button,
            double=double,
            timestamp=time.time(),
            success=True
        )

        # Record click
        self.click_history.append(event)
        self.last_click = event

        # In real implementation, would call Windows API (SendInput or mouse_event)
        # For testing, we just record the event

        return event

    def left_click(self, x: float, y: float, **kwargs) -> ClickEvent:
        """Convenience method for left click"""
        return self.click(x, y, button=MouseButton.LEFT, **kwargs)

    def right_click(self, x: float, y: float, **kwargs) -> ClickEvent:
        """Convenience method for right click"""
        return self.click(x, y, button=MouseButton.RIGHT, **kwargs)

    def middle_click(self, x: float, y: float, **kwargs) -> ClickEvent:
        """Convenience method for middle click"""
        return self.click(x, y, button=MouseButton.MIDDLE, **kwargs)

    def double_click(self, x: float, y: float, **kwargs) -> ClickEvent:
        """Convenience method for double click"""
        return self.click(x, y, button=MouseButton.LEFT, double=True, **kwargs)

    def get_click_count(self, button: Optional[MouseButton] = None) -> int:
        """Get number of clicks executed"""
        if button is None:
            return len(self.click_history)

        return sum(1 for event in self.click_history if event.button == button)

    def clear_history(self):
        """Clear click history"""
        self.click_history = []
        self.last_click = None


# ============================================================================
# Test Class: Coordinate Validation
# ============================================================================

class TestCoordinateValidator:
    """Test coordinate validation"""

    def test_validator_creation(self):
        """Test creating coordinate validator"""
        validator = CoordinateValidator(1920, 1080, margin=10)

        assert validator.screen_width == 1920
        assert validator.screen_height == 1080
        assert validator.margin == 10

    def test_valid_coordinates(self):
        """Test validating valid coordinates"""
        validator = CoordinateValidator(1920, 1080, margin=0)

        assert validator.is_valid(960, 540) is True
        assert validator.is_valid(0, 0) is True
        assert validator.is_valid(1920, 1080) is True

    def test_invalid_coordinates_negative(self):
        """Test that negative coordinates are invalid"""
        validator = CoordinateValidator(1920, 1080, margin=0)

        assert validator.is_valid(-10, 540) is False
        assert validator.is_valid(960, -10) is False

    def test_invalid_coordinates_too_large(self):
        """Test that coordinates beyond screen are invalid"""
        validator = CoordinateValidator(1920, 1080, margin=0)

        assert validator.is_valid(2000, 540) is False
        assert validator.is_valid(960, 1200) is False

    def test_margin_validation(self):
        """Test validation with safety margin"""
        validator = CoordinateValidator(1920, 1080, margin=50)

        # Just inside margin - invalid
        assert validator.is_valid(40, 500) is False
        assert validator.is_valid(500, 40) is False

        # Just outside margin - valid
        assert validator.is_valid(60, 500) is True
        assert validator.is_valid(500, 60) is True

        # Near right/bottom edge with margin
        assert validator.is_valid(1880, 500) is False  # Too close to right (1920-50=1870)
        assert validator.is_valid(500, 1040) is False  # Too close to bottom (1080-50=1030)

    def test_validate_with_error_message(self):
        """Test detailed validation with error messages"""
        validator = CoordinateValidator(1920, 1080, margin=10)

        # Valid coordinates
        is_valid, msg = validator.validate(960, 540)
        assert is_valid is True
        assert msg == ""

        # Invalid - too far left
        is_valid, msg = validator.validate(5, 540)
        assert is_valid is False
        assert "left edge" in msg.lower()

        # Invalid - too far down
        is_valid, msg = validator.validate(960, 1075)
        assert is_valid is False
        assert "bottom edge" in msg.lower()

    def test_clamp_coordinates(self):
        """Test clamping out-of-bounds coordinates"""
        validator = CoordinateValidator(1920, 1080, margin=10)

        # Clamp negative
        x, y = validator.clamp(-50, 540)
        assert x == 10  # Clamped to margin
        assert y == 540

        # Clamp too large
        x, y = validator.clamp(2000, 1100)
        assert x == 1910  # Clamped to width - margin
        assert y == 1070  # Clamped to height - margin

        # Already valid - no change
        x, y = validator.clamp(960, 540)
        assert x == 960
        assert y == 540


# ============================================================================
# Test Class: Click Execution
# ============================================================================

class TestClickExecutor:
    """Test click execution"""

    def test_executor_creation(self):
        """Test creating click executor"""
        executor = ClickExecutor(1920, 1080, validate_coords=True, safety_margin=10)

        assert executor.screen_width == 1920
        assert executor.screen_height == 1080
        assert executor.validate_coords is True
        assert executor.safety_margin == 10

    def test_simple_click(self):
        """Test executing a simple click"""
        executor = ClickExecutor()

        event = executor.click(500, 300)

        assert event.x == 500
        assert event.y == 300
        assert event.button == MouseButton.LEFT
        assert event.double is False
        assert event.success is True

    def test_click_recorded_in_history(self):
        """Test that clicks are recorded in history"""
        executor = ClickExecutor()

        executor.click(500, 300)
        executor.click(600, 400)

        assert len(executor.click_history) == 2
        assert executor.last_click.x == 600
        assert executor.last_click.y == 400

    def test_left_click_convenience(self):
        """Test left click convenience method"""
        executor = ClickExecutor()

        event = executor.left_click(500, 300)

        assert event.button == MouseButton.LEFT
        assert event.x == 500

    def test_right_click_convenience(self):
        """Test right click convenience method"""
        executor = ClickExecutor()

        event = executor.right_click(500, 300)

        assert event.button == MouseButton.RIGHT

    def test_middle_click_convenience(self):
        """Test middle click convenience method"""
        executor = ClickExecutor()

        event = executor.middle_click(500, 300)

        assert event.button == MouseButton.MIDDLE

    def test_double_click_convenience(self):
        """Test double click convenience method"""
        executor = ClickExecutor()

        event = executor.double_click(500, 300)

        assert event.button == MouseButton.LEFT
        assert event.double is True

    def test_click_invalid_coordinates_raises_error(self):
        """Test that invalid coordinates raise error"""
        executor = ClickExecutor(1920, 1080, validate_coords=True, safety_margin=10)

        # Too far left
        with pytest.raises(ValueError, match="Invalid coordinates"):
            executor.click(5, 500)

        # Too far down
        with pytest.raises(ValueError, match="Invalid coordinates"):
            executor.click(500, 1075)

    def test_click_with_validation_disabled(self):
        """Test clicking with validation disabled"""
        executor = ClickExecutor(validate_coords=False)

        # Should not raise error even with invalid coordinates
        event = executor.click(-100, 5000)

        assert event.success is True
        assert event.x == -100
        assert event.y == 5000

    def test_click_with_auto_clamp(self):
        """Test clicking with automatic clamping"""
        executor = ClickExecutor(1920, 1080, safety_margin=10)

        # Out of bounds coordinates with auto_clamp
        event = executor.click(2000, 1100, auto_clamp=True)

        # Should be clamped to valid range
        assert event.x == 1910  # 1920 - 10
        assert event.y == 1070  # 1080 - 10
        assert event.success is True

    def test_get_click_count_all(self):
        """Test getting total click count"""
        executor = ClickExecutor()

        executor.left_click(100, 100)
        executor.right_click(200, 200)
        executor.middle_click(300, 300)

        assert executor.get_click_count() == 3

    def test_get_click_count_by_button(self):
        """Test getting click count by button type"""
        executor = ClickExecutor()

        executor.left_click(100, 100)
        executor.left_click(150, 150)
        executor.right_click(200, 200)
        executor.middle_click(300, 300)

        assert executor.get_click_count(MouseButton.LEFT) == 2
        assert executor.get_click_count(MouseButton.RIGHT) == 1
        assert executor.get_click_count(MouseButton.MIDDLE) == 1

    def test_clear_history(self):
        """Test clearing click history"""
        executor = ClickExecutor()

        executor.click(100, 100)
        executor.click(200, 200)

        assert len(executor.click_history) == 2

        executor.clear_history()

        assert len(executor.click_history) == 0
        assert executor.last_click is None


# ============================================================================
# Test Class: Button Types
# ============================================================================

class TestButtonTypes:
    """Test different mouse button types"""

    def test_all_button_types(self):
        """Test clicking with all button types"""
        executor = ClickExecutor()

        left_event = executor.click(100, 100, button=MouseButton.LEFT)
        right_event = executor.click(200, 200, button=MouseButton.RIGHT)
        middle_event = executor.click(300, 300, button=MouseButton.MIDDLE)

        assert left_event.button == MouseButton.LEFT
        assert right_event.button == MouseButton.RIGHT
        assert middle_event.button == MouseButton.MIDDLE

    def test_single_vs_double_click(self):
        """Test single vs double click"""
        executor = ClickExecutor()

        single = executor.click(100, 100, double=False)
        double = executor.click(200, 200, double=True)

        assert single.double is False
        assert double.double is True

    def test_button_enum_values(self):
        """Test MouseButton enum values"""
        assert MouseButton.LEFT.value == "left"
        assert MouseButton.RIGHT.value == "right"
        assert MouseButton.MIDDLE.value == "middle"


# ============================================================================
# Test Class: Click Accuracy
# ============================================================================

class TestClickAccuracy:
    """Test click accuracy and coordinate precision"""

    def test_click_preserves_coordinates(self):
        """Test that click preserves exact coordinates"""
        executor = ClickExecutor()

        x, y = 123.456, 789.012
        event = executor.click(x, y)

        assert event.x == x
        assert event.y == y

    def test_click_with_calibrated_coordinates(self, mock_calibration):
        """Test clicking with calibrated coordinates"""
        executor = ClickExecutor()

        # Simulate OCR measurement with known offset
        true_coord = np.array([500, 400])
        offset = np.array([3.5, -2.8])
        measured = true_coord + offset

        # Apply calibration
        mock_calibration.offset = offset
        mock_calibration.is_calibrated = True
        corrected = mock_calibration.correct(measured)

        # Click corrected coordinate
        event = executor.click(corrected[0], corrected[1])

        # Should be very close to true coordinate
        assert abs(event.x - true_coord[0]) < 0.1
        assert abs(event.y - true_coord[1]) < 0.1

    def test_click_accuracy_within_bounds(self, random_coordinates):
        """Test that all clicks are within screen bounds"""
        executor = ClickExecutor(1920, 1080, safety_margin=20)

        coords = random_coordinates(n_points=50, margin=50, seed=42)

        for coord in coords:
            event = executor.click(coord[0], coord[1])

            # All should be within bounds
            assert 20 <= event.x <= 1900
            assert 20 <= event.y <= 1060


# ============================================================================
# Test Class: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_click_at_screen_edges(self):
        """Test clicking at screen edges"""
        executor = ClickExecutor(1920, 1080, safety_margin=0)

        # Top-left corner
        event = executor.click(0, 0)
        assert event.success is True

        # Bottom-right corner
        event = executor.click(1920, 1080)
        assert event.success is True

    def test_click_with_safety_margin_at_edges(self):
        """Test that safety margin prevents edge clicks"""
        executor = ClickExecutor(1920, 1080, safety_margin=10)

        # Too close to edge - should fail without auto_clamp
        with pytest.raises(ValueError):
            executor.click(5, 500)

        # With auto_clamp - should succeed
        event = executor.click(5, 500, auto_clamp=True)
        assert event.x == 10  # Clamped to margin
        assert event.success is True

    def test_click_with_nan_coordinates(self):
        """Test handling of NaN coordinates"""
        executor = ClickExecutor(validate_coords=False)

        # With validation disabled, should record NaN
        event = executor.click(float('nan'), float('nan'))
        assert event.success is True

    def test_click_with_infinity_coordinates(self):
        """Test handling of infinity coordinates"""
        executor = ClickExecutor(validate_coords=False)

        event = executor.click(float('inf'), float('inf'))
        assert event.success is True


# ============================================================================
# Test Class: Performance
# ============================================================================

@pytest.mark.performance
class TestClickPerformance:
    """Test click execution performance"""

    def test_rapid_clicking(self, benchmark_timer):
        """Test rapid click execution"""
        executor = ClickExecutor()

        # Execute many clicks rapidly
        _, elapsed = benchmark_timer.time_function(
            'rapid_clicks',
            lambda: [executor.click(i*10, i*10) for i in range(1000)],
        )

        # Should be very fast (< 10ms for 1000 clicks in mock mode)
        assert elapsed < 0.01

    def test_validation_overhead(self, random_coordinates, benchmark_timer):
        """Test overhead of coordinate validation"""
        coords = random_coordinates(n_points=1000, margin=100)

        # Without validation
        executor_no_val = ClickExecutor(validate_coords=False)
        _, time_no_val = benchmark_timer.time_function(
            'clicks_no_validation',
            lambda: [executor_no_val.click(c[0], c[1]) for c in coords]
        )

        # With validation
        executor_val = ClickExecutor(validate_coords=True)
        _, time_val = benchmark_timer.time_function(
            'clicks_with_validation',
            lambda: [executor_val.click(c[0], c[1]) for c in coords]
        )

        # Validation should add minimal overhead (< 2x)
        assert time_val < time_no_val * 2


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestClickExecutorIntegration:
    """Integration tests for click executor"""

    def test_end_to_end_click_workflow(self, ocr_simulator,
                                       mock_calibration,
                                       random_coordinates):
        """Test complete click workflow with OCR and calibration"""
        # Setup
        executor = ClickExecutor(1920, 1080, safety_margin=10)

        # Calibrate
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Test clicks
        test_true = random_coordinates(n_points=10, seed=99)
        test_measured = ocr_simulator.measure_batch(test_true)

        click_events = []
        for measured, true in zip(test_measured, test_true):
            # Apply calibration
            corrected = mock_calibration.correct(measured)

            # Execute click
            event = executor.click(corrected[0], corrected[1])
            click_events.append(event)

        # All clicks should succeed
        assert all(event.success for event in click_events)
        assert len(click_events) == 10

    def test_multi_button_clicking_sequence(self):
        """Test sequence of different button clicks"""
        executor = ClickExecutor()

        # Simulate UI interaction sequence
        executor.left_click(500, 300)        # Click button
        executor.right_click(600, 400)       # Open context menu
        executor.left_click(620, 450)        # Select menu item
        executor.double_click(700, 500)      # Double-click to open
        executor.middle_click(800, 300)      # Middle-click link

        # Verify sequence
        assert len(executor.click_history) == 5
        assert executor.click_history[0].button == MouseButton.LEFT
        assert executor.click_history[1].button == MouseButton.RIGHT
        assert executor.click_history[3].double is True
        assert executor.click_history[4].button == MouseButton.MIDDLE

    def test_window_clicking_scenario(self, mock_windows):
        """Test clicking UI elements in different windows"""
        executor = ClickExecutor()

        # Click elements in each window
        for window in mock_windows:
            # Click center of window
            center_x = window.x + window.width / 2
            center_y = window.y + window.height / 2

            event = executor.click(center_x, center_y)

            # Verify click is within window bounds
            assert window.contains_point(event.x, event.y)

    def test_accuracy_validation_with_real_coordinates(self,
                                                       ocr_simulator,
                                                       mock_calibration,
                                                       random_coordinates,
                                                       calculate_accuracy_metrics):
        """Test that clicks maintain high accuracy"""
        executor = ClickExecutor()

        # Calibrate
        calib_true = random_coordinates(n_points=30, seed=42)
        calib_measured = ocr_simulator.measure_batch(calib_true)
        mock_calibration.calibrate(calib_measured, calib_true)

        # Test clicks
        test_true = random_coordinates(n_points=100, seed=99)
        test_measured = ocr_simulator.measure_batch(test_true)

        clicked_coords = []
        for measured in test_measured:
            corrected = mock_calibration.correct(measured)
            event = executor.click(corrected[0], corrected[1])
            clicked_coords.append([event.x, event.y])

        # Calculate accuracy
        metrics = calculate_accuracy_metrics(test_true, np.array(clicked_coords))

        # Should maintain high accuracy
        assert metrics['within_2px'] >= 0.99
        assert metrics['mean_error'] < 1.0
