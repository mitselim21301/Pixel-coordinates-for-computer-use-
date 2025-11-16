#!/usr/bin/env python3
"""
Example: Basic Click on Text

Demonstrates the simplest usage of the Accurate Click system:
finding and clicking on text on the screen.

This example shows:
- System initialization
- Finding text with OCR
- Clicking on detected text
- Error handling
"""

from mcp_accurate_click_server import AccurateClickSystem
import sys


def main():
    print("=" * 60)
    print("Basic Click Example")
    print("=" * 60)

    # Step 1: Initialize the system
    print("\n[1/3] Initializing Accurate Click System...")
    system = AccurateClickSystem(
        use_calibration=False,  # No calibration for quick demo
        use_gpu=False           # Use CPU (change to True if GPU available)
    )
    print("✓ System initialized")

    # Step 2: Get system information
    print("\n[2/3] Getting system information...")
    info = system.get_system_info()

    print(f"\nDetected {len(info['monitors'])} monitor(s):")
    for i, monitor in enumerate(info['monitors']):
        print(f"  Monitor {i}:")
        print(f"    Resolution: {monitor['resolution'][0]}×{monitor['resolution'][1]}")
        print(f"    DPI: {monitor['dpi'][0]} ({monitor['scale']*100:.0f}% scaling)")
        print(f"    Primary: {'Yes' if monitor['primary'] else 'No'}")

    # Step 3: Click on text
    print("\n[3/3] Clicking on text...")
    print("\nLooking for text on screen...")

    # Example: Click on common UI elements
    # Try multiple common texts to demonstrate
    texts_to_try = [
        "File",
        "Edit",
        "Start",
        "Submit",
        "OK",
        "Cancel"
    ]

    found = False
    for text in texts_to_try:
        print(f"\nTrying to find: '{text}'")

        success = system.click_on_text(
            text=text,
            min_confidence=0.7  # Lower threshold for fuzzy matching
        )

        if success:
            print(f"✓ Found and clicked '{text}'!")
            found = True
            break
        else:
            print(f"✗ '{text}' not found")

    if not found:
        print("\n⚠ No common UI elements found on screen.")
        print("   Make sure you have a window open with text visible.")
        print("\n   You can also try clicking on specific text:")
        print("   >>> system.click_on_text('YourTextHere')")

        # Show what text IS on screen
        print("\n   Detected text on screen:")
        elements = system.get_screen_text(min_confidence=0.7)
        if elements:
            for i, elem in enumerate(elements[:10]):  # Show first 10
                print(f"     - '{elem['text']}' (confidence: {elem['confidence']:.1%})")
            if len(elements) > 10:
                print(f"     ... and {len(elements) - 10} more")
        else:
            print("     (No text detected)")

        return 1

    print("\n" + "=" * 60)
    print("✓ Example completed successfully!")
    print("=" * 60)
    return 0


def example_with_specific_text():
    """
    Alternative example: Click on specific text you know is on screen
    """
    print("\nExample: Click on specific text")
    print("-" * 40)

    # Initialize system
    system = AccurateClickSystem()

    # Define the text you want to click
    target_text = "Submit"  # Change this to text on your screen

    print(f"Looking for '{target_text}' on screen...")

    # Click on the text
    success = system.click_on_text(
        text=target_text,
        min_confidence=0.8,  # Higher confidence for exact match
        monitor=0            # Search on all monitors
    )

    if success:
        print(f"✓ Successfully clicked '{target_text}'!")
    else:
        print(f"✗ Could not find '{target_text}' on screen")
        print("   Try lowering min_confidence or check text is visible")

    return 0 if success else 1


def example_with_coordinates():
    """
    Alternative example: Click at specific coordinates
    """
    print("\nExample: Click at specific coordinates")
    print("-" * 40)

    # Initialize system
    system = AccurateClickSystem()

    # Define coordinates (center of 1920x1080 screen)
    x, y = 960, 540

    print(f"Clicking at coordinates ({x}, {y})...")

    # Execute click
    success = system.click_at_coordinates(x, y)

    if success:
        print(f"✓ Successfully clicked at ({x}, {y})!")
    else:
        print(f"✗ Click failed at ({x}, {y})")

    return 0 if success else 1


if __name__ == "__main__":
    # Run main example
    exit_code = main()

    # Uncomment to run alternative examples:
    # exit_code = example_with_specific_text()
    # exit_code = example_with_coordinates()

    sys.exit(exit_code)
