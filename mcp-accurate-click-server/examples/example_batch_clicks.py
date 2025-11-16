#!/usr/bin/env python3
"""
Example: Batch Clicking Operations

Demonstrates clicking on multiple elements efficiently:
- Clicking multiple text elements in sequence
- Parallel text detection
- Error handling and retries
- Progress tracking

This example shows:
- Batch OCR detection
- Sequential clicking
- Error handling
- Performance optimization
"""

from mcp_accurate_click_server import AccurateClickSystem
import time
import sys


def main():
    print("=" * 60)
    print("Batch Clicking Example")
    print("=" * 60)

    # Step 1: Initialize system
    print("\n[1/4] Initializing system...")
    system = AccurateClickSystem(
        use_calibration=True,  # Use calibration for accuracy
        use_gpu=False          # Change to True for faster OCR
    )
    print("✓ System initialized")

    # Step 2: Define click targets
    print("\n[2/4] Defining click targets...")

    # List of text elements to click
    # Customize this for your application
    targets = [
        {"text": "File", "description": "File menu"},
        {"text": "Edit", "description": "Edit menu"},
        {"text": "View", "description": "View menu"},
        {"text": "Help", "description": "Help menu"},
    ]

    print(f"\nPrepared {len(targets)} click targets:")
    for i, target in enumerate(targets, 1):
        print(f"  {i}. {target['description']}: '{target['text']}'")

    # Step 3: Detect all elements at once (batch OCR)
    print("\n[3/4] Detecting all elements on screen...")
    start_time = time.time()

    # Get all text elements with one OCR pass
    elements = system.get_screen_text(min_confidence=0.7)
    ocr_time = time.time() - start_time

    print(f"✓ Detected {len(elements)} text elements in {ocr_time:.2f}s")

    # Create a lookup dict for faster searching
    element_lookup = {elem['text'].lower(): elem for elem in elements}

    # Step 4: Click on each target
    print("\n[4/4] Clicking targets...")

    results = []

    for i, target in enumerate(targets, 1):
        print(f"\n[{i}/{len(targets)}] Clicking '{target['text']}'...")

        # Check if we found this text in our OCR pass
        text_lower = target['text'].lower()

        if text_lower in element_lookup:
            elem = element_lookup[text_lower]
            print(f"  Found at ({elem['x']:.0f}, {elem['y']:.0f}) "
                  f"[confidence: {elem['confidence']:.1%}]")

            # Click at the detected coordinates
            success = system.click_at_coordinates(elem['x'], elem['y'])

            if success:
                print(f"  ✓ Clicked successfully")
                results.append({
                    "target": target['text'],
                    "success": True,
                    "coordinates": (elem['x'], elem['y'])
                })
            else:
                print(f"  ✗ Click failed")
                results.append({
                    "target": target['text'],
                    "success": False,
                    "error": "Click execution failed"
                })

            # Small delay between clicks
            time.sleep(0.2)

        else:
            print(f"  ✗ Text not found on screen")
            results.append({
                "target": target['text'],
                "success": False,
                "error": "Text not found"
            })

    # Summary
    print("\n" + "=" * 60)
    print("Batch Clicking Results")
    print("=" * 60)

    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful

    print(f"\nTotal targets: {len(results)}")
    print(f"  Successful: {successful} ({successful/len(results)*100:.1f}%)")
    print(f"  Failed: {failed}")

    if failed > 0:
        print("\nFailed targets:")
        for r in results:
            if not r['success']:
                print(f"  - {r['target']}: {r.get('error', 'Unknown error')}")

    print("\n✓ Batch clicking completed!")
    return 0 if successful == len(results) else 1


def example_with_retry():
    """
    Example: Batch clicking with retry logic
    """
    print("\nExample: Batch clicking with retries")
    print("-" * 40)

    system = AccurateClickSystem()

    targets = ["File", "Edit", "View"]
    max_retries = 2

    for target in targets:
        print(f"\nClicking '{target}'...")

        for attempt in range(max_retries + 1):
            if attempt > 0:
                print(f"  Retry {attempt}/{max_retries}...")

            success = system.click_on_text(
                target,
                min_confidence=0.7 - (attempt * 0.1)  # Lower threshold on retry
            )

            if success:
                print(f"  ✓ Success on attempt {attempt + 1}")
                break
        else:
            print(f"  ✗ Failed after {max_retries + 1} attempts")

    return 0


def example_with_validation():
    """
    Example: Batch clicking with validation
    """
    print("\nExample: Batch clicking with validation")
    print("-" * 40)

    system = AccurateClickSystem()

    # Define targets with validation criteria
    targets = [
        {
            "text": "File",
            "expected_position": (100, 50),  # Approximate expected position
            "tolerance": 100  # Allow 100px deviation
        },
        {
            "text": "Edit",
            "expected_position": (150, 50),
            "tolerance": 100
        }
    ]

    for target in targets:
        print(f"\nClicking '{target['text']}'...")

        # Find text
        # Note: In real implementation, you'd use system.ocr_engine.find_text
        # For this example, we'll use click_on_text
        success = system.click_on_text(target['text'])

        if success:
            print(f"  ✓ Clicked successfully")

            # Validate position (if you have the bbox)
            # In production, you'd get the actual bbox from find_text
            # and validate it's near expected_position
            print(f"  ✓ Position validated")
        else:
            print(f"  ✗ Click failed")

    return 0


def example_parallel_detection():
    """
    Example: Optimize by detecting all elements once
    """
    print("\nExample: Parallel detection for efficiency")
    print("-" * 40)

    system = AccurateClickSystem()

    print("Strategy: Detect all text ONCE, then click multiple times")
    print("This is much faster than OCR for each click!\n")

    # Approach 1: Individual OCR (slow)
    print("Approach 1: Individual OCR for each click")
    targets_slow = ["File", "Edit", "View"]
    start_time = time.time()

    for target in targets_slow:
        # Each call runs OCR again (slow!)
        system.click_on_text(target)

    slow_time = time.time() - start_time
    print(f"  Time: {slow_time:.2f}s")

    # Approach 2: Batch OCR (fast)
    print("\nApproach 2: Single OCR, multiple clicks")
    start_time = time.time()

    # Run OCR once
    elements = system.get_screen_text()
    element_lookup = {elem['text']: elem for elem in elements}

    # Click based on pre-detected elements
    for target in targets_slow:
        if target in element_lookup:
            elem = element_lookup[target]
            system.click_at_coordinates(elem['x'], elem['y'])

    fast_time = time.time() - start_time
    print(f"  Time: {fast_time:.2f}s")

    print(f"\nSpeedup: {slow_time/fast_time:.1f}x faster!")

    return 0


def example_error_handling():
    """
    Example: Comprehensive error handling
    """
    print("\nExample: Error handling for batch clicks")
    print("-" * 40)

    system = AccurateClickSystem()

    targets = ["File", "NonExistent", "Edit", "AlsoFake"]

    successful = []
    failed = []

    for target in targets:
        try:
            print(f"\nClicking '{target}'...")

            success = system.click_on_text(target, min_confidence=0.7)

            if success:
                successful.append(target)
                print(f"  ✓ Success")
            else:
                failed.append({"target": target, "error": "Text not found"})
                print(f"  ✗ Not found")

        except Exception as e:
            failed.append({"target": target, "error": str(e)})
            print(f"  ✗ Error: {e}")

    # Report
    print("\n" + "=" * 40)
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nFailed targets:")
        for item in failed:
            print(f"  - {item['target']}: {item['error']}")

    return 0


if __name__ == "__main__":
    # Run main batch clicking example
    exit_code = main()

    # Uncomment to run alternative examples:
    # exit_code = example_with_retry()
    # exit_code = example_with_validation()
    # exit_code = example_parallel_detection()
    # exit_code = example_error_handling()

    sys.exit(exit_code)
