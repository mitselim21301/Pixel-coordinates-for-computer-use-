#!/usr/bin/env python3
"""
Example: Multi-Monitor Setup

Demonstrates working with multiple monitors:
- Detecting monitors
- Clicking on specific monitors
- Handling virtual desktop coordinates
- Multi-monitor calibration

This example shows:
- Monitor enumeration and information
- Clicking on text on specific monitors
- Virtual desktop coordinate handling
"""

from mcp_accurate_click_server import AccurateClickSystem
import sys


def main():
    print("=" * 60)
    print("Multi-Monitor Setup Example")
    print("=" * 60)

    # Step 1: Initialize system
    print("\n[1/4] Initializing system...")
    system = AccurateClickSystem(use_calibration=False)
    print("✓ System initialized")

    # Step 2: Get monitor information
    print("\n[2/4] Detecting monitors...")
    info = system.get_system_info()

    num_monitors = len(info['monitors'])
    print(f"\n✓ Detected {num_monitors} monitor(s)")

    if num_monitors == 1:
        print("\n⚠ Single monitor detected.")
        print("   This example is more interesting with multiple monitors,")
        print("   but will still demonstrate the concepts.")

    # Display detailed monitor information
    print("\nMonitor Configuration:")
    print("-" * 60)

    for i, monitor in enumerate(info['monitors']):
        print(f"\nMonitor {i}:")
        print(f"  Position: ({monitor['bounds'][0]}, {monitor['bounds'][1]}) "
              f"to ({monitor['bounds'][2]}, {monitor['bounds'][3]})")
        print(f"  Resolution: {monitor['resolution'][0]}×{monitor['resolution'][1]}")
        print(f"  DPI: {monitor['dpi'][0]} × {monitor['dpi'][1]} "
              f"({monitor['scale']*100:.0f}% scaling)")
        print(f"  Primary: {'Yes' if monitor['primary'] else 'No'}")

        # Calculate monitor center
        center_x = (monitor['bounds'][0] + monitor['bounds'][2]) // 2
        center_y = (monitor['bounds'][1] + monitor['bounds'][3]) // 2
        print(f"  Center: ({center_x}, {center_y})")

    # Display virtual desktop information
    print("\nVirtual Desktop:")
    vscreen = info['virtual_screen']
    print(f"  Position: ({vscreen['left']}, {vscreen['top']})")
    print(f"  Size: {vscreen['width']}×{vscreen['height']}")
    print(f"  Bounds: ({vscreen['left']}, {vscreen['top']}) to "
          f"({vscreen['left'] + vscreen['width']}, {vscreen['top'] + vscreen['height']})")

    # Step 3: Search for text on each monitor
    print("\n[3/4] Searching for text on each monitor...")

    for i, monitor in enumerate(info['monitors']):
        print(f"\nMonitor {i}:")

        # Get text elements on this monitor
        try:
            elements = system.get_screen_text(
                monitor=i if i > 0 else 0,  # 0 = all monitors, 1+ = specific
                min_confidence=0.7
            )

            print(f"  Found {len(elements)} text element(s)")

            # Display first 5 elements
            for j, elem in enumerate(elements[:5]):
                print(f"    {j+1}. '{elem['text'][:30]}...' "
                      f"at ({elem['x']:.0f}, {elem['y']:.0f}) "
                      f"[confidence: {elem['confidence']:.1%}]")

            if len(elements) > 5:
                print(f"    ... and {len(elements) - 5} more")

        except Exception as e:
            print(f"  Error: {e}")

    # Step 4: Click on text on specific monitor
    print("\n[4/4] Clicking on specific monitor...")

    if num_monitors > 1:
        print("\nExample: Click on text on Monitor 1 (secondary)")

        # Define which monitor to click on
        target_monitor = 1

        # Try to click on common text on that monitor
        test_texts = ["File", "Edit", "Start", "OK", "Cancel"]

        for text in test_texts:
            print(f"\nLooking for '{text}' on Monitor {target_monitor}...")
            success = system.click_on_text(
                text=text,
                monitor=target_monitor,
                min_confidence=0.7
            )

            if success:
                print(f"✓ Successfully clicked '{text}' on Monitor {target_monitor}!")
                break
        else:
            print(f"✗ No test text found on Monitor {target_monitor}")
    else:
        print("\nSingle monitor setup - clicking on Monitor 0...")

        # Try to click on text
        success = system.click_on_text("File", min_confidence=0.7)
        if success:
            print("✓ Successfully clicked 'File'!")
        else:
            print("✗ 'File' not found")

    print("\n" + "=" * 60)
    print("✓ Multi-monitor example completed!")
    print("=" * 60)

    return 0


def example_virtual_desktop_coordinates():
    """
    Example: Understanding virtual desktop coordinates
    """
    print("\nExample: Virtual desktop coordinates")
    print("-" * 40)

    system = AccurateClickSystem()
    info = system.get_system_info()

    print("\nVirtual Desktop Coordinate System:")
    print("=" * 40)

    # Explain virtual desktop
    print("\nIn multi-monitor setups, Windows uses a 'virtual desktop'")
    print("where monitors are positioned in a coordinate system.")
    print("\nExample layout:")
    print("  ┌───────────┐ ┌───────────┐")
    print("  │ Monitor 0 │ │ Monitor 1 │")
    print("  │ (Primary) │ │           │")
    print("  │   (0,0)   │ │ (1920,0)  │")
    print("  └───────────┘ └───────────┘")

    print("\nYour configuration:")
    for monitor in info['monitors']:
        print(f"\n  Monitor {monitor['index']}:")
        print(f"    Top-left: ({monitor['bounds'][0]}, {monitor['bounds'][1]})")
        print(f"    Bottom-right: ({monitor['bounds'][2]}, {monitor['bounds'][3]})")

        # Example point in center of monitor
        center_x = (monitor['bounds'][0] + monitor['bounds'][2]) // 2
        center_y = (monitor['bounds'][1] + monitor['bounds'][3]) // 2
        print(f"    Center: ({center_x}, {center_y})")

        # Click example
        print(f"\n    To click center of Monitor {monitor['index']}:")
        print(f"      system.click_at_coordinates({center_x}, {center_y})")

    return 0


def example_multi_monitor_calibration():
    """
    Example: Calibration for multi-monitor setups
    """
    print("\nExample: Multi-monitor calibration")
    print("-" * 40)

    system = AccurateClickSystem(use_calibration=True)
    info = system.get_system_info()

    num_monitors = len(info['monitors'])

    print(f"\nDetected {num_monitors} monitor(s)")

    if num_monitors == 1:
        print("Single monitor - using standard calibration")
        points_per_monitor = 20
    else:
        print("Multiple monitors detected!")
        print("\nRecommendation:")
        print("  - Use 20-30 calibration points per monitor")
        print("  - Distribute points across all monitors")
        points_per_monitor = 20

    total_points = points_per_monitor * num_monitors

    print(f"\nRunning calibration with {total_points} total points...")
    print(f"  ({points_per_monitor} points per monitor)")

    try:
        # Run calibration
        system.calibrate_system(num_points=total_points)

        # Check results
        status = system.get_calibration_status()
        print("\n✓ Multi-monitor calibration completed!")
        print(f"  Mean error: {status['calibration']['mean_error']:.2f}px")
        print("  This calibration works across all monitors!")

        return 0
    except Exception as e:
        print(f"✗ Calibration failed: {e}")
        return 1


def example_click_across_monitors():
    """
    Example: Click on elements across multiple monitors
    """
    print("\nExample: Click across multiple monitors")
    print("-" * 40)

    system = AccurateClickSystem()
    info = system.get_system_info()

    # Define test pattern: click center of each monitor
    print("\nClicking center of each monitor...")

    for i, monitor in enumerate(info['monitors']):
        # Calculate center
        center_x = (monitor['bounds'][0] + monitor['bounds'][2]) // 2
        center_y = (monitor['bounds'][1] + monitor['bounds'][3]) // 2

        print(f"\nMonitor {i}: Clicking at ({center_x}, {center_y})")

        success = system.click_at_coordinates(center_x, center_y)

        if success:
            print(f"  ✓ Clicked successfully")
        else:
            print(f"  ✗ Click failed")

    return 0


if __name__ == "__main__":
    # Run main multi-monitor example
    exit_code = main()

    # Uncomment to run alternative examples:
    # exit_code = example_virtual_desktop_coordinates()
    # exit_code = example_multi_monitor_calibration()
    # exit_code = example_click_across_monitors()

    sys.exit(exit_code)
