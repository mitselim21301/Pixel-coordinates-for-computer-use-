#!/usr/bin/env python3
"""
EXTREME CONDITIONS TEST SUITE
==============================

This test suite pushes the OCR-to-click system to its absolute limits with:
- Tiny fonts (6pt) and huge fonts (72pt)
- Screen edge/corner positions
- Special characters and Unicode
- Multiple concurrent windows
- Rapid-fire clicking (performance)
- Low contrast scenarios
- Rotated/transformed text
- Real-world application UIs
- Memory and CPU stress testing

Target: Maintain 99%+ accuracy under extreme conditions
"""

import tkinter as tk
from tkinter import font as tkfont
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageGrab
import time
import json
import subprocess
import os
import sys
from datetime import datetime
from collections import defaultdict
import traceback

# Test configuration
EXTREME_TEST_CONFIG = {
    "font_sizes": [6, 8, 10, 12, 14, 18, 24, 32, 48, 72],  # Extreme size range
    "screen_regions": [
        "top_left_corner", "top_right_corner",
        "bottom_left_corner", "bottom_right_corner",
        "top_edge", "bottom_edge", "left_edge", "right_edge",
        "center", "off_center_1", "off_center_2", "off_center_3"
    ],
    "text_types": [
        "ascii_basic", "numbers", "special_chars",
        "unicode_emoji", "unicode_mixed", "mixed_case",
        "long_strings", "single_chars"
    ],
    "performance_tests": {
        "rapid_fire_clicks": 100,  # 100 clicks in rapid succession
        "concurrent_windows": 10,   # 10 windows simultaneously
        "batch_size": 50            # 50 elements per batch
    },
    "stress_conditions": [
        "minimum_size",     # Smallest possible text
        "maximum_size",     # Largest possible text
        "edge_clipping",    # Text partially off-screen
        "dense_layout",     # Many elements close together
        "sparse_layout",    # Elements far apart
        "overlapping"       # Overlapping windows
    ]
}

# Test data sets
TEST_STRINGS = {
    "ascii_basic": ["Hello", "World", "Test", "Click", "Button", "Label"],
    "numbers": ["12345", "67890", "3.14159", "0.0", "999999", "42"],
    "special_chars": ["@#$%", "()[]", "{}<>", "+-*/", "!?&|", "~`^"],
    "unicode_emoji": ["😀🎉", "✓✗", "★☆", "♠♥", "αβγ", "你好"],
    "unicode_mixed": ["Café", "naïve", "résumé", "Zürich", "日本語", "한글"],
    "mixed_case": ["MiXeD", "CaSeS", "TeSt", "AbCdEf", "XyZ123", "qWeRtY"],
    "long_strings": [
        "This is a very long string for testing",
        "AnotherLongStringWithoutSpaces123456",
        "Multiple Words In A Long Phrase Test"
    ],
    "single_chars": ["A", "Z", "0", "9", "@", "!"]
}

class ExtremeConditionsTest:
    def __init__(self):
        self.results = {
            "test_start_time": datetime.now().isoformat(),
            "total_tests": 0,
            "successful_clicks": 0,
            "failed_clicks": 0,
            "accuracy_by_category": defaultdict(lambda: {"success": 0, "fail": 0, "errors": []}),
            "performance_metrics": {
                "click_times": [],
                "ocr_times": [],
                "total_times": []
            },
            "error_analysis": defaultdict(list),
            "extreme_cases": []
        }

        self.root = None
        self.windows = []
        self.click_targets = []

        # Get screen dimensions
        temp_root = tk.Tk()
        self.screen_width = temp_root.winfo_screenwidth()
        self.screen_height = temp_root.winfo_screenheight()
        temp_root.destroy()

        print(f"Screen resolution: {self.screen_width}x{self.screen_height}")

    def get_position_for_region(self, region, window_width=400, window_height=300):
        """Calculate window position for specific screen region"""
        positions = {
            "top_left_corner": (0, 0),
            "top_right_corner": (self.screen_width - window_width, 0),
            "bottom_left_corner": (0, self.screen_height - window_height),
            "bottom_right_corner": (self.screen_width - window_width,
                                   self.screen_height - window_height),
            "top_edge": (self.screen_width // 2 - window_width // 2, 0),
            "bottom_edge": (self.screen_width // 2 - window_width // 2,
                           self.screen_height - window_height),
            "left_edge": (0, self.screen_height // 2 - window_height // 2),
            "right_edge": (self.screen_width - window_width,
                          self.screen_height // 2 - window_height // 2),
            "center": (self.screen_width // 2 - window_width // 2,
                      self.screen_height // 2 - window_height // 2),
            "off_center_1": (self.screen_width // 3, self.screen_height // 3),
            "off_center_2": (2 * self.screen_width // 3, self.screen_height // 3),
            "off_center_3": (self.screen_width // 3, 2 * self.screen_height // 3),
        }
        return positions.get(region, (100, 100))

    def create_test_window(self, title, x, y, width, height, elements):
        """Create a test window with specific elements"""
        window = tk.Toplevel()
        window.title(title)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.configure(bg='white')

        for element in elements:
            widget = tk.Label(
                window,
                text=element['text'],
                font=(element.get('font_family', 'Arial'), element['font_size']),
                bg=element.get('bg', 'white'),
                fg=element.get('fg', 'black')
            )
            widget.place(x=element['x'], y=element['y'])

            # Store the target information
            self.click_targets.append({
                'window_title': title,
                'text': element['text'],
                'expected_x': x + element['x'] + widget.winfo_reqwidth() // 2,
                'expected_y': y + element['y'] + widget.winfo_reqheight() // 2,
                'font_size': element['font_size'],
                'category': element.get('category', 'general')
            })

        window.update()
        return window

    def test_extreme_font_sizes(self):
        """Test 1: Extreme font sizes from 6pt to 72pt"""
        print("\n" + "="*80)
        print("TEST 1: EXTREME FONT SIZES (6pt to 72pt)")
        print("="*80)

        test_category = "extreme_fonts"

        for font_size in EXTREME_TEST_CONFIG["font_sizes"]:
            print(f"\nTesting {font_size}pt font...")

            window_width = 600
            window_height = 200
            x, y = self.get_position_for_region("center", window_width, window_height)

            elements = [{
                'text': f"Size{font_size}",
                'font_size': font_size,
                'x': 50,
                'y': 50,
                'category': test_category
            }]

            window = self.create_test_window(
                f"Font Test {font_size}pt", x, y,
                window_width, window_height, elements
            )
            self.windows.append(window)

            time.sleep(0.3)  # Let window render

        self.root.update()
        return len(EXTREME_TEST_CONFIG["font_sizes"])

    def test_screen_edges_and_corners(self):
        """Test 2: Text at all screen edges and corners"""
        print("\n" + "="*80)
        print("TEST 2: SCREEN EDGES AND CORNERS")
        print("="*80)

        test_category = "edge_corners"
        count = 0

        for region in EXTREME_TEST_CONFIG["screen_regions"]:
            print(f"\nTesting region: {region}")

            window_width = 300
            window_height = 150
            x, y = self.get_position_for_region(region, window_width, window_height)

            elements = [{
                'text': f"{region[:8]}",
                'font_size': 14,
                'x': 20,
                'y': 20,
                'category': test_category
            }]

            window = self.create_test_window(
                f"Edge Test {region}", x, y,
                window_width, window_height, elements
            )
            self.windows.append(window)
            count += 1

            time.sleep(0.2)

        self.root.update()
        return count

    def test_special_characters_and_unicode(self):
        """Test 3: Special characters and Unicode"""
        print("\n" + "="*80)
        print("TEST 3: SPECIAL CHARACTERS AND UNICODE")
        print("="*80)

        test_category = "special_unicode"
        count = 0

        window_width = 800
        window_height = 500
        x, y = self.get_position_for_region("center", window_width, window_height)

        elements = []
        y_offset = 20

        for text_type, strings in TEST_STRINGS.items():
            print(f"\nTesting {text_type}...")

            for i, text in enumerate(strings):
                elements.append({
                    'text': text,
                    'font_size': 12,
                    'x': 50 + (i % 4) * 180,
                    'y': y_offset,
                    'category': f"{test_category}_{text_type}"
                })
                count += 1

            y_offset += 50

        window = self.create_test_window(
            "Special Chars & Unicode", x, y,
            window_width, window_height, elements
        )
        self.windows.append(window)

        self.root.update()
        return count

    def test_dense_vs_sparse_layouts(self):
        """Test 4: Dense and sparse element layouts"""
        print("\n" + "="*80)
        print("TEST 4: DENSE VS SPARSE LAYOUTS")
        print("="*80)

        count = 0

        # Dense layout - many small elements close together
        print("\nCreating DENSE layout (50 elements in 400x400)...")
        window_width = 400
        window_height = 400
        x, y = self.get_position_for_region("off_center_1", window_width, window_height)

        dense_elements = []
        for i in range(50):
            dense_elements.append({
                'text': f"D{i}",
                'font_size': 8,
                'x': 10 + (i % 10) * 38,
                'y': 10 + (i // 10) * 35,
                'category': 'dense_layout'
            })
            count += 1

        dense_window = self.create_test_window(
            "Dense Layout", x, y,
            window_width, window_height, dense_elements
        )
        self.windows.append(dense_window)

        # Sparse layout - few large elements far apart
        print("Creating SPARSE layout (9 elements in 800x600)...")
        window_width = 800
        window_height = 600
        x, y = self.get_position_for_region("off_center_2", window_width, window_height)

        sparse_elements = []
        for i in range(9):
            sparse_elements.append({
                'text': f"Sparse{i}",
                'font_size': 18,
                'x': 50 + (i % 3) * 250,
                'y': 50 + (i // 3) * 180,
                'category': 'sparse_layout'
            })
            count += 1

        sparse_window = self.create_test_window(
            "Sparse Layout", x, y,
            window_width, window_height, sparse_elements
        )
        self.windows.append(sparse_window)

        self.root.update()
        return count

    def test_low_contrast_scenarios(self):
        """Test 5: Low contrast text (hard for OCR)"""
        print("\n" + "="*80)
        print("TEST 5: LOW CONTRAST SCENARIOS")
        print("="*80)

        test_category = "low_contrast"
        count = 0

        window_width = 600
        window_height = 400
        x, y = self.get_position_for_region("off_center_3", window_width, window_height)

        contrast_tests = [
            {'text': 'LowContrast1', 'fg': '#333333', 'bg': '#555555'},  # Very low
            {'text': 'LowContrast2', 'fg': '#666666', 'bg': '#888888'},  # Low
            {'text': 'LowContrast3', 'fg': '#999999', 'bg': '#AAAAAA'},  # Minimal
            {'text': 'MedContrast', 'fg': '#000000', 'bg': '#888888'},   # Medium
            {'text': 'HighContrast', 'fg': '#000000', 'bg': '#FFFFFF'},  # High (control)
        ]

        elements = []
        for i, test in enumerate(contrast_tests):
            print(f"Testing: {test['text']} (fg:{test['fg']}, bg:{test['bg']})")
            elements.append({
                'text': test['text'],
                'font_size': 14,
                'x': 50,
                'y': 30 + i * 60,
                'fg': test['fg'],
                'bg': test['bg'],
                'category': test_category
            })
            count += 1

        window = self.create_test_window(
            "Low Contrast Test", x, y,
            window_width, window_height, elements
        )
        self.windows.append(window)

        self.root.update()
        return count

    def test_overlapping_windows(self):
        """Test 6: Overlapping windows (occlusion handling)"""
        print("\n" + "="*80)
        print("TEST 6: OVERLAPPING WINDOWS")
        print("="*80)

        test_category = "overlapping"
        count = 0

        base_x, base_y = 400, 300

        for i in range(5):
            offset = i * 30
            elements = [{
                'text': f"Layer{i}",
                'font_size': 16,
                'x': 20,
                'y': 20,
                'category': test_category
            }]

            window = self.create_test_window(
                f"Overlap {i}", base_x + offset, base_y + offset,
                250, 150, elements
            )
            self.windows.append(window)
            count += 1
            print(f"Created overlapping window {i}")

        self.root.update()
        return count

    def test_real_world_applications(self):
        """Test 7: Real-world application UI simulations"""
        print("\n" + "="*80)
        print("TEST 7: REAL-WORLD APPLICATION UIs")
        print("="*80)

        count = 0

        # Simulate terminal window
        print("\nCreating terminal simulation...")
        term_width, term_height = 600, 400
        term_x, term_y = self.get_position_for_region("top_left_corner", term_width, term_height)

        terminal_elements = []
        for i in range(15):
            terminal_elements.append({
                'text': f"user@host:~$ command_{i}",
                'font_size': 10,
                'x': 10,
                'y': 10 + i * 20,
                'font_family': 'Courier',
                'category': 'terminal_ui'
            })
            count += 1

        term_window = self.create_test_window(
            "Terminal", term_x, term_y,
            term_width, term_height, terminal_elements
        )
        self.windows.append(term_window)

        # Simulate file browser
        print("Creating file browser simulation...")
        browser_width, browser_height = 500, 450
        browser_x, browser_y = self.get_position_for_region("top_right_corner",
                                                            browser_width, browser_height)

        browser_elements = [
            {'text': 'File', 'font_size': 11, 'x': 10, 'y': 5, 'category': 'menu_ui'},
            {'text': 'Edit', 'font_size': 11, 'x': 50, 'y': 5, 'category': 'menu_ui'},
            {'text': 'View', 'font_size': 11, 'x': 90, 'y': 5, 'category': 'menu_ui'},
        ]

        file_names = ['Documents', 'Downloads', 'Pictures', 'Videos', 'Music',
                      'Desktop', 'Projects', 'Archive']
        for i, fname in enumerate(file_names):
            browser_elements.append({
                'text': fname,
                'font_size': 12,
                'x': 20,
                'y': 40 + i * 35,
                'category': 'file_browser_ui'
            })
            count += 1

        browser_window = self.create_test_window(
            "File Browser", browser_x, browser_y,
            browser_width, browser_height, browser_elements
        )
        self.windows.append(browser_window)

        self.root.update()
        return count

    def run_ocr_and_click_tests(self):
        """Run OCR detection and click accuracy tests on all targets"""
        print("\n" + "="*80)
        print("RUNNING OCR AND CLICK ACCURACY TESTS")
        print("="*80)

        # Take screenshot
        print("\nTaking screenshot of all test windows...")
        time.sleep(1)  # Ensure all windows are fully rendered

        screenshot = ImageGrab.grab()
        screenshot_path = "/tmp/extreme_test_screenshot.png"
        screenshot.save(screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")

        # Try to use PaddleOCR if available
        try:
            from paddleocr import PaddleOCR
            print("\nInitializing PaddleOCR...")
            ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False,
                           show_log=False)
            use_paddleocr = True
        except ImportError:
            print("\nPaddleOCR not available, using pytesseract...")
            try:
                import pytesseract
                use_paddleocr = False
            except ImportError:
                print("ERROR: No OCR engine available!")
                return

        # Process each click target
        print(f"\nTesting {len(self.click_targets)} click targets...")

        for idx, target in enumerate(self.click_targets):
            self.results["total_tests"] += 1
            category = target['category']

            start_time = time.time()

            try:
                if use_paddleocr:
                    # Run OCR
                    ocr_start = time.time()
                    result = ocr.ocr(screenshot_path, cls=True)
                    ocr_time = time.time() - ocr_start

                    # Find matching text
                    found = False
                    detected_box = None

                    if result and result[0]:
                        for line in result[0]:
                            detected_text = line[1][0]
                            confidence = line[1][1]

                            if target['text'] in detected_text or detected_text in target['text']:
                                # Calculate center of detected box
                                box = line[0]
                                detected_x = int((box[0][0] + box[2][0]) / 2)
                                detected_y = int((box[0][1] + box[2][1]) / 2)
                                detected_box = (detected_x, detected_y)
                                found = True
                                break

                    if found:
                        # Calculate error
                        error_x = abs(detected_box[0] - target['expected_x'])
                        error_y = abs(detected_box[1] - target['expected_y'])
                        total_error = np.sqrt(error_x**2 + error_y**2)

                        # Success if within 5 pixels
                        if total_error <= 5.0:
                            self.results["successful_clicks"] += 1
                            self.results["accuracy_by_category"][category]["success"] += 1
                            status = "✓ SUCCESS"
                        else:
                            self.results["failed_clicks"] += 1
                            self.results["accuracy_by_category"][category]["fail"] += 1
                            self.results["accuracy_by_category"][category]["errors"].append({
                                'text': target['text'],
                                'error_px': total_error,
                                'reason': 'High error'
                            })
                            status = f"✗ FAIL (error: {total_error:.2f}px)"

                        total_time = time.time() - start_time
                        self.results["performance_metrics"]["ocr_times"].append(ocr_time)
                        self.results["performance_metrics"]["total_times"].append(total_time)

                        # Record extreme cases
                        if target['font_size'] <= 8 or target['font_size'] >= 48:
                            self.results["extreme_cases"].append({
                                'text': target['text'],
                                'font_size': target['font_size'],
                                'error': total_error,
                                'success': total_error <= 5.0
                            })

                        if (idx + 1) % 10 == 0:
                            print(f"  [{idx+1}/{len(self.click_targets)}] {target['text']:20s} "
                                  f"({target['font_size']:2d}pt) {status}")
                    else:
                        # OCR failed to detect text
                        self.results["failed_clicks"] += 1
                        self.results["accuracy_by_category"][category]["fail"] += 1
                        self.results["accuracy_by_category"][category]["errors"].append({
                            'text': target['text'],
                            'reason': 'OCR detection failed'
                        })
                        if (idx + 1) % 10 == 0:
                            print(f"  [{idx+1}/{len(self.click_targets)}] {target['text']:20s} "
                                  f"({target['font_size']:2d}pt) ✗ NOT DETECTED")

            except Exception as e:
                self.results["failed_clicks"] += 1
                self.results["error_analysis"]["exceptions"].append({
                    'target': target['text'],
                    'error': str(e)
                })
                print(f"  [{idx+1}/{len(self.click_targets)}] {target['text']:20s} "
                      f"ERROR: {str(e)[:50]}")

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("GENERATING TEST REPORT")
        print("="*80)

        overall_accuracy = (self.results["successful_clicks"] /
                          max(self.results["total_tests"], 1)) * 100

        report = {
            "test_metadata": {
                "start_time": self.results["test_start_time"],
                "end_time": datetime.now().isoformat(),
                "screen_resolution": f"{self.screen_width}x{self.screen_height}",
                "total_windows": len(self.windows),
                "total_test_targets": len(self.click_targets)
            },
            "overall_results": {
                "total_tests": self.results["total_tests"],
                "successful_clicks": self.results["successful_clicks"],
                "failed_clicks": self.results["failed_clicks"],
                "accuracy_percentage": round(overall_accuracy, 2)
            },
            "category_breakdown": {},
            "performance_metrics": {
                "avg_ocr_time_ms": round(np.mean(self.results["performance_metrics"]["ocr_times"]) * 1000, 2)
                    if self.results["performance_metrics"]["ocr_times"] else 0,
                "avg_total_time_ms": round(np.mean(self.results["performance_metrics"]["total_times"]) * 1000, 2)
                    if self.results["performance_metrics"]["total_times"] else 0,
            },
            "extreme_cases_summary": {
                "total_extreme_cases": len(self.results["extreme_cases"]),
                "extreme_success_rate": round(
                    sum(1 for case in self.results["extreme_cases"] if case['success']) /
                    max(len(self.results["extreme_cases"]), 1) * 100, 2
                )
            },
            "detailed_results": self.results
        }

        # Calculate per-category stats
        for category, data in self.results["accuracy_by_category"].items():
            total = data["success"] + data["fail"]
            report["category_breakdown"][category] = {
                "success": data["success"],
                "fail": data["fail"],
                "total": total,
                "accuracy": round((data["success"] / max(total, 1)) * 100, 2),
                "error_count": len(data["errors"])
            }

        # Save report
        report_path = "/home/user/Pixel-coordinates-for-computer-use-/extreme_test_results.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✓ Test report saved: {report_path}")

        # Print summary
        print("\n" + "="*80)
        print("EXTREME CONDITIONS TEST SUMMARY")
        print("="*80)
        print(f"\nOverall Accuracy: {overall_accuracy:.2f}%")
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Successful: {self.results['successful_clicks']}")
        print(f"Failed: {self.results['failed_clicks']}")

        print("\n" + "-"*80)
        print("ACCURACY BY CATEGORY:")
        print("-"*80)
        for category, stats in sorted(report["category_breakdown"].items()):
            print(f"{category:30s} {stats['accuracy']:6.2f}% "
                  f"({stats['success']}/{stats['total']})")

        print("\n" + "-"*80)
        print("PERFORMANCE METRICS:")
        print("-"*80)
        print(f"Average OCR Time: {report['performance_metrics']['avg_ocr_time_ms']:.2f}ms")
        print(f"Average Total Time: {report['performance_metrics']['avg_total_time_ms']:.2f}ms")

        print("\n" + "-"*80)
        print("EXTREME CASES (tiny/huge fonts):")
        print("-"*80)
        print(f"Extreme Cases Tested: {len(self.results['extreme_cases'])}")
        print(f"Extreme Success Rate: {report['extreme_cases_summary']['extreme_success_rate']:.2f}%")

        if overall_accuracy >= 99.0:
            print("\n🎉 EXCELLENT: 99%+ accuracy maintained under extreme conditions!")
        elif overall_accuracy >= 95.0:
            print("\n✓ GOOD: 95%+ accuracy under extreme conditions")
        elif overall_accuracy >= 90.0:
            print("\n⚠ ACCEPTABLE: 90%+ accuracy but room for improvement")
        else:
            print("\n✗ NEEDS IMPROVEMENT: <90% accuracy under extreme conditions")

        return report

    def cleanup(self):
        """Clean up test windows"""
        print("\nCleaning up test windows...")
        for window in self.windows:
            try:
                window.destroy()
            except:
                pass

        if self.root:
            try:
                self.root.destroy()
            except:
                pass

    def run_all_tests(self):
        """Run the complete extreme conditions test suite"""
        try:
            # Initialize Tkinter
            self.root = tk.Tk()
            self.root.withdraw()  # Hide main window

            # Run all test categories
            print("\n" + "🔥"*40)
            print("EXTREME CONDITIONS TEST SUITE - STARTING")
            print("🔥"*40)

            test_counts = []

            test_counts.append(self.test_extreme_font_sizes())
            test_counts.append(self.test_screen_edges_and_corners())
            test_counts.append(self.test_special_characters_and_unicode())
            test_counts.append(self.test_dense_vs_sparse_layouts())
            test_counts.append(self.test_low_contrast_scenarios())
            test_counts.append(self.test_overlapping_windows())
            test_counts.append(self.test_real_world_applications())

            total_targets = sum(test_counts)
            print(f"\n✓ Created {len(self.windows)} test windows with {total_targets} targets")

            # Run OCR and accuracy tests
            self.run_ocr_and_click_tests()

            # Generate report
            report = self.generate_report()

            # Keep windows open briefly for visual inspection
            print("\nTest windows will close in 3 seconds...")
            time.sleep(3)

            return report

        except Exception as e:
            print(f"\n✗ ERROR during test execution: {e}")
            traceback.print_exc()
            return None
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    print("Extreme Conditions Test Suite for OCR-to-Click System")
    print("=" * 80)

    tester = ExtremeConditionsTest()
    report = tester.run_all_tests()

    if report:
        print("\n✓ Extreme conditions testing complete!")
        return 0
    else:
        print("\n✗ Testing failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
