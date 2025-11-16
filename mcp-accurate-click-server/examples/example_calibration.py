#!/usr/bin/env python3
"""
Example: Calibration Workflow

Demonstrates the calibration process to achieve sub-pixel accuracy.

This example shows:
- Running calibration with different numbers of points
- Saving and loading calibration
- Comparing accuracy before/after calibration
- Checking calibration status
"""

from mcp_accurate_click_server import AccurateClickSystem
import numpy as np
import sys
import os


def main():
    print("=" * 60)
    print("Calibration Workflow Example")
    print("=" * 60)

    # Step 1: Initialize system
    print("\n[1/5] Initializing system...")
    system = AccurateClickSystem(use_calibration=True, use_gpu=False)
    print("✓ System initialized with calibration enabled")

    # Step 2: Check initial calibration status
    print("\n[2/5] Checking initial calibration status...")
    status = system.get_calibration_status()

    if status['is_calibrated']:
        print("✓ System is already calibrated!")
        print(f"  Number of points: {status['calibration']['num_points']}")
        print(f"  Mean error: {status['calibration']['mean_error']:.2f}px")
        print(f"  File: {status.get('file_loaded', 'N/A')}")

        response = input("\nRecalibrate anyway? (y/N): ")
        if response.lower() != 'y':
            print("Using existing calibration.")
            return 0
    else:
        print("✗ System is not calibrated")
        print("  Running calibration will improve accuracy from ~4.5px to ~0.7px")

    # Step 3: Run calibration
    print("\n[3/5] Running calibration...")
    print("\nCalibration Options:")
    print("  1. Quick calibration (20 points, ~30 seconds)")
    print("  2. Standard calibration (50 points, ~75 seconds)")
    print("  3. High-accuracy calibration (100 points, ~150 seconds)")

    choice = input("\nSelect option (1-3) [default: 1]: ").strip() or "1"

    num_points_map = {"1": 20, "2": 50, "3": 100}
    num_points = num_points_map.get(choice, 20)

    print(f"\nRunning calibration with {num_points} points...")
    print("Instructions:")
    print("  - Calibration points will be displayed on your screen")
    print("  - Click on each crosshair as accurately as possible")
    print("  - This typically takes {:.0f} seconds".format(num_points * 1.5))

    try:
        # Run calibration
        system.calibrate_system(num_points=num_points)

        # Check calibration results
        status = system.get_calibration_status()
        print("\n✓ Calibration completed successfully!")
        print(f"  Points used: {status['calibration']['num_points']}")
        print(f"  Mean error: {status['calibration']['mean_error']:.2f}px")
        print(f"  Median error: {status['calibration']['median_error']:.2f}px")
        print(f"  Max error: {status['calibration']['max_error']:.2f}px")

        # Interpret results
        mean_error = status['calibration']['mean_error']
        if mean_error < 0.5:
            print("  Quality: ⭐⭐⭐⭐⭐ Excellent (sub-pixel precision!)")
        elif mean_error < 1.0:
            print("  Quality: ⭐⭐⭐⭐ Very Good")
        elif mean_error < 2.0:
            print("  Quality: ⭐⭐⭐ Good")
        else:
            print("  Quality: ⭐⭐ Fair (consider recalibrating)")

    except Exception as e:
        print(f"✗ Calibration failed: {e}")
        return 1

    # Step 4: Save calibration
    print("\n[4/5] Saving calibration...")

    # Use a default calibration file in user's home directory
    calibration_dir = os.path.expanduser("~/.mcp_accurate_click")
    os.makedirs(calibration_dir, exist_ok=True)
    calibration_file = os.path.join(calibration_dir, "calibration.npz")

    try:
        system.calibration.save_calibration(calibration_file)
        print(f"✓ Calibration saved to: {calibration_file}")
        print(f"  This file can be loaded in future sessions to skip calibration")
    except Exception as e:
        print(f"✗ Failed to save calibration: {e}")

    # Step 5: Test calibrated clicking
    print("\n[5/5] Testing calibrated clicking...")
    print("\nNow trying to click with calibration enabled...")

    # Try to click on common text
    test_texts = ["File", "Edit", "Start", "OK"]

    for text in test_texts:
        success = system.click_on_text(text, min_confidence=0.7)
        if success:
            print(f"✓ Successfully clicked '{text}' with calibration!")
            break
    else:
        print("⚠ No test text found. Calibration is still active for future clicks.")

    print("\n" + "=" * 60)
    print("✓ Calibration workflow completed!")
    print("=" * 60)
    print("\nNext steps:")
    print(f"  - Your calibration is saved to: {calibration_file}")
    print("  - Future sessions will auto-load this calibration")
    print("  - Recalibrate if you change DPI settings or monitors")

    return 0


def example_load_calibration():
    """
    Example: Load existing calibration
    """
    print("\nExample: Load existing calibration")
    print("-" * 40)

    # Initialize system
    system = AccurateClickSystem(use_calibration=True)

    # Define calibration file path
    calibration_file = os.path.expanduser("~/.mcp_accurate_click/calibration.npz")

    # Check if calibration file exists
    if not os.path.exists(calibration_file):
        print(f"✗ Calibration file not found: {calibration_file}")
        print("  Run calibration first (example_calibration.py)")
        return 1

    # Load calibration
    print(f"Loading calibration from: {calibration_file}")
    try:
        system.calibration.load_calibration(calibration_file)
        print("✓ Calibration loaded successfully!")

        # Check status
        status = system.get_calibration_status()
        print(f"  Points: {status['calibration']['num_points']}")
        print(f"  Mean error: {status['calibration']['mean_error']:.2f}px")

        return 0
    except Exception as e:
        print(f"✗ Failed to load calibration: {e}")
        return 1


def example_compare_accuracy():
    """
    Example: Compare accuracy with and without calibration
    """
    print("\nExample: Compare accuracy with/without calibration")
    print("-" * 40)

    # Define test points
    test_points = [
        (500, 500),
        (1000, 500),
        (1500, 500),
        (500, 1000),
        (1000, 1000),
        (1500, 1000)
    ]

    # Simulate OCR measurements (with systematic error)
    systematic_error = (3.5, -2.8)
    random_noise = 0.5

    measurements = []
    for x, y in test_points:
        # Add systematic error + random noise
        measured_x = x + systematic_error[0] + np.random.randn() * random_noise
        measured_y = y + systematic_error[1] + np.random.randn() * random_noise
        measurements.append((measured_x, measured_y))

    print("\nTest points (simulated):")
    print("True → Measured (uncalibrated)")
    for i, (true_point, measured) in enumerate(zip(test_points, measurements)):
        error = np.sqrt((measured[0] - true_point[0])**2 +
                       (measured[1] - true_point[1])**2)
        print(f"  {i+1}. ({true_point[0]:4.0f}, {true_point[1]:4.0f}) → "
              f"({measured[0]:6.1f}, {measured[1]:6.1f}) "
              f"[error: {error:.2f}px]")

    # Calculate uncalibrated errors
    uncal_errors = [
        np.sqrt((m[0] - t[0])**2 + (m[1] - t[1])**2)
        for m, t in zip(measurements, test_points)
    ]

    print(f"\nWithout calibration:")
    print(f"  Mean error: {np.mean(uncal_errors):.2f}px")
    print(f"  Max error: {np.max(uncal_errors):.2f}px")

    # Now with calibration (simple offset correction)
    offset_x = np.mean([m[0] - t[0] for m, t in zip(measurements, test_points)])
    offset_y = np.mean([m[1] - t[1] for m, t in zip(measurements, test_points)])

    corrected = [(m[0] - offset_x, m[1] - offset_y) for m in measurements]
    cal_errors = [
        np.sqrt((c[0] - t[0])**2 + (c[1] - t[1])**2)
        for c, t in zip(corrected, test_points)
    ]

    print(f"\nWith calibration:")
    print(f"  Offset correction: ({offset_x:.2f}, {offset_y:.2f})")
    print(f"  Mean error: {np.mean(cal_errors):.2f}px")
    print(f"  Max error: {np.max(cal_errors):.2f}px")

    print(f"\nImprovement: {(1 - np.mean(cal_errors)/np.mean(uncal_errors))*100:.1f}% error reduction!")

    return 0


if __name__ == "__main__":
    # Run main calibration workflow
    exit_code = main()

    # Uncomment to run alternative examples:
    # exit_code = example_load_calibration()
    # exit_code = example_compare_accuracy()

    sys.exit(exit_code)
