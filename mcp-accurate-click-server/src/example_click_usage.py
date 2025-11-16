#!/usr/bin/env python3
"""
Example Usage of Click Executor
Demonstrates various click execution patterns
"""

import time
import sys
from click_executor import (
    get_platform_executor,
    get_executor,
    click,
    double_click,
    right_click,
    get_cursor_position,
    WindowsClickExecutor,
    LinuxClickExecutor,
)


def example_1_basic_usage():
    """Example 1: Basic click operations"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Click Operations")
    print("="*70)

    # Get current cursor position
    x, y = get_cursor_position()
    print(f"\nCurrent cursor position: ({x}, {y})")

    # Note: Actual clicking is commented out to avoid accidental clicks
    # Uncomment to test real clicking

    # Example coordinates (adjust for your screen)
    # test_x, test_y = 500, 500

    # Single click
    # print(f"\nClicking at ({test_x}, {test_y})...")
    # success = click(test_x, test_y)
    # print(f"Result: {'Success' if success else 'Failed'}")

    # Double click
    # print(f"\nDouble-clicking at ({test_x}, {test_y})...")
    # success = double_click(test_x, test_y)
    # print(f"Result: {'Success' if success else 'Failed'}")

    # Right click
    # print(f"\nRight-clicking at ({test_x}, {test_y})...")
    # success = right_click(test_x, test_y)
    # print(f"Result: {'Success' if success else 'Failed'}")

    print("\n✓ Basic usage examples complete (click code commented out)")


def example_2_executor_instance():
    """Example 2: Using executor instance"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Using Executor Instance")
    print("="*70)

    # Get executor (singleton pattern)
    executor = get_executor()
    print(f"\nExecutor type: {executor.__class__.__name__}")
    print(f"Platform: {executor.platform_name}")

    # Get cursor position
    x, y = executor.get_cursor_position()
    print(f"Cursor position: ({x}, {y})")

    # Click with different buttons (commented out)
    # executor.click(100, 100, button='left')
    # executor.click(200, 200, button='middle')
    # executor.click(300, 300, button='right')

    print("\n✓ Executor instance examples complete")


def example_3_platform_specific():
    """Example 3: Platform-specific operations"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Platform-Specific Operations")
    print("="*70)

    executor = get_platform_executor()

    if isinstance(executor, WindowsClickExecutor):
        print("\nWindows-specific features:")

        # Get virtual desktop bounds
        bounds = executor._get_virtual_screen_bounds()
        print(f"  Virtual desktop bounds:")
        print(f"    Left: {bounds['left']}")
        print(f"    Top: {bounds['top']}")
        print(f"    Width: {bounds['width']}")
        print(f"    Height: {bounds['height']}")

        # Show normalization example
        test_x, test_y = bounds['width'] // 2, bounds['height'] // 2
        x_adj = test_x - bounds['left']
        y_adj = test_y - bounds['top']
        x_norm = (x_adj * 65535) // bounds['width']
        y_norm = (y_adj * 65535) // bounds['height']

        print(f"\n  Example coordinate normalization:")
        print(f"    Physical: ({test_x}, {test_y})")
        print(f"    Adjusted: ({x_adj}, {y_adj})")
        print(f"    Normalized: ({x_norm}, {y_norm})")

    elif isinstance(executor, LinuxClickExecutor):
        print("\nLinux-specific features:")

        # Show X11 display info
        print(f"  X11 Display: {executor.display}")
        print(f"  Screen: {executor.screen}")
        print(f"  Screen dimensions: {executor.screen.width_in_pixels}x{executor.screen.height_in_pixels}")

    print("\n✓ Platform-specific examples complete")


def example_4_error_handling():
    """Example 4: Proper error handling"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Error Handling")
    print("="*70)

    try:
        # Initialize executor
        executor = get_platform_executor()
        print(f"\n✓ Executor initialized: {executor.__class__.__name__}")

        # Try to get cursor position
        try:
            x, y = executor.get_cursor_position()
            print(f"✓ Cursor position: ({x}, {y})")
        except Exception as e:
            print(f"✗ Failed to get cursor position: {e}")

        # Try to click (commented out)
        # try:
        #     success = executor.click(100, 100)
        #     if success:
        #         print("✓ Click successful")
        #     else:
        #         print("✗ Click failed")
        # except Exception as e:
        #     print(f"✗ Click error: {e}")

    except RuntimeError as e:
        print(f"\n✗ Failed to initialize executor: {e}")
        print("  This might happen if:")
        print("  - Running on unsupported platform")
        print("  - Missing dependencies (e.g., python-xlib on Linux)")
        print("  - No display available (e.g., headless server)")

    print("\n✓ Error handling examples complete")


def example_5_sequential_clicks():
    """Example 5: Sequential click operations"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Sequential Click Operations")
    print("="*70)

    executor = get_executor()

    # Define a sequence of click operations
    click_sequence = [
        {'x': 100, 'y': 100, 'button': 'left', 'delay': 0.5},
        {'x': 200, 'y': 200, 'button': 'left', 'delay': 0.5},
        {'x': 300, 'y': 300, 'button': 'right', 'delay': 0.5},
    ]

    print("\nClick sequence defined (commented out for safety):")
    for i, op in enumerate(click_sequence, 1):
        print(f"  {i}. Click {op['button']} at ({op['x']}, {op['y']}), wait {op['delay']}s")

    # Execute sequence (commented out)
    # for op in click_sequence:
    #     print(f"\nExecuting: {op['button']} click at ({op['x']}, {op['y']})")
    #     success = executor.click(op['x'], op['y'], button=op['button'])
    #     print(f"Result: {'Success' if success else 'Failed'}")
    #     time.sleep(op['delay'])

    print("\n✓ Sequential click examples complete")


def example_6_coordinate_validation():
    """Example 6: Coordinate validation"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Coordinate Validation")
    print("="*70)

    executor = get_executor()

    # Get screen bounds
    if isinstance(executor, WindowsClickExecutor):
        bounds = executor._get_virtual_screen_bounds()
        max_x = bounds['left'] + bounds['width']
        max_y = bounds['top'] + bounds['height']
        min_x = bounds['left']
        min_y = bounds['top']
    else:
        # For Linux, use screen dimensions
        try:
            max_x = executor.screen.width_in_pixels
            max_y = executor.screen.height_in_pixels
            min_x = 0
            min_y = 0
        except:
            # Fallback to common resolution
            max_x = 1920
            max_y = 1080
            min_x = 0
            min_y = 0

    print(f"\nScreen bounds:")
    print(f"  X: {min_x} to {max_x}")
    print(f"  Y: {min_y} to {max_y}")

    # Test coordinates
    test_coords = [
        (100, 100, True),       # Valid
        (500, 500, True),       # Valid
        (-100, -100, False),    # May be valid on multi-monitor
        (10000, 10000, False),  # Likely invalid
    ]

    print("\nValidating coordinates:")
    for x, y, should_be_valid in test_coords:
        is_valid = (min_x <= x <= max_x and min_y <= y <= max_y)
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"  ({x:5d}, {y:5d}): {status}")

    print("\n✓ Coordinate validation examples complete")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("CLICK EXECUTOR - USAGE EXAMPLES")
    print("="*70)
    print("\nNOTE: Actual clicking is commented out to prevent accidental clicks.")
    print("Uncomment the click lines in each example to test real clicking.")
    print("\nPress Ctrl+C to stop at any time.")
    print("="*70)

    try:
        example_1_basic_usage()
        example_2_executor_instance()
        example_3_platform_specific()
        example_4_error_handling()
        example_5_sequential_clicks()
        example_6_coordinate_validation()

        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETE")
        print("="*70)
        print("\nTo test actual clicking:")
        print("1. Open this file in an editor")
        print("2. Uncomment the click lines in the examples")
        print("3. Adjust coordinates to match your screen")
        print("4. Run the script again")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
