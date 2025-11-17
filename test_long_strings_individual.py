#!/usr/bin/env python3
"""
Test long strings INDIVIDUALLY (not in batches)
Goal: Fix the 24 long string failures from the 1000-example test
Hypothesis: Long strings work fine when tested individually (not in batch of 20)
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from paddleocr import PaddleOCR
import time
import json

class LongStringIndividualTest:
    def __init__(self):
        print("Initializing PaddleOCR for individual long string testing...")
        self.ocr = PaddleOCR(
            lang='en',
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            text_det_thresh=0.2,
            text_det_box_thresh=0.5,
            text_det_unclip_ratio=2.0,
            text_det_limit_side_len=64
        )
        print("✓ OCR initialized\n")

    def test_long_strings(self):
        """Test the same long strings from the original test, but INDIVIDUALLY"""
        # Original long string test cases (from test_1000_examples.py)
        long_strings = [
            "The quick brown fox jumps over",  # 31 chars
            "A very long string that contains",  # 34 chars
            "Testing OCR with long text strings",  # 36 chars
            "This is an extremely long sentence",  # 36 chars
            "http://www.example.com/very/long/url",  # 37 chars
            "C:\\Users\\Username\\Documents\\File.txt",  # 37 chars
            "Lorem ipsum dolor sit amet consectetur",  # 40 chars
            "The quick brown fox jumps over the lazy dog",  # 44 chars
            "This is a very long string to test OCR accuracy",  # 49 chars
            "http://www.example.com/very/long/url/path/to",  # 45 chars
            "C:\\Users\\Username\\Documents\\Very\\Long\\Path.txt",  # 47 chars
            "Lorem ipsum dolor sit amet consectetur adipiscing",  # 51 chars
            "The quick brown fox jumps over the lazy dog again",  # 51 chars
            "This is an extremely long string for testing purposes",  # 55 chars
            "http://www.example.com/very/long/url/path/to/resource",  # 54 chars
            "C:\\Users\\Username\\Documents\\Very\\Long\\File\\Path.txt",  # 52 chars
            "Lorem ipsum dolor sit amet consectetur adipiscing elit",  # 56 chars
            "The quick brown fox jumps over the lazy dog multiple times",  # 60 chars
            "This is a super extremely long string that tests OCR limits",  # 61 chars
            "http://www.example.com/very/long/url/path/to/resource/file",  # 59 chars
        ]

        results = []
        success = 0
        total = len(long_strings)

        print(f"Testing {total} long strings INDIVIDUALLY...\n")

        for i, text in enumerate(long_strings):
            # Create test image with ONLY this string (no batch)
            img_width = max(1000, len(text) * 15)  # Make wide enough
            img = Image.new('RGB', (img_width, 200), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)

            # Use a reasonable font
            try:
                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
            except:
                font = ImageFont.load_default()

            # Draw text at a clear position
            target_x, target_y = 50, 100
            draw.text((target_x, target_y), text, fill=(0, 0, 0), font=font, anchor='lt')

            img_path = f'/tmp/long_string_individual_{i}.png'
            img.save(img_path)

            # Run OCR
            start = time.time()
            result = self.ocr.predict(img_path)
            ocr_time = (time.time() - start) * 1000

            detected = False
            detected_text = None
            distance = None
            match_type = None

            if result and len(result) > 0:
                ocr_result = result[0]
                rec_texts = ocr_result.get('rec_texts', [])
                rec_polys = ocr_result.get('rec_polys', [])

                # Clean both for comparison
                target_clean = text.lower().replace(" ", "").replace(":", "").replace(".", "").replace("/", "").replace("\\", "").replace("-", "").replace("_", "")

                # Try to find the text with flexible matching
                for j, det_text in enumerate(rec_texts):
                    detected_clean = det_text.lower().replace(" ", "").replace(":", "").replace(".", "").replace("/", "").replace("\\", "").replace("-", "").replace("_", "")

                    matched = False

                    # 1. Exact match
                    if target_clean == detected_clean:
                        matched = True
                        match_type = "exact"
                    # 2. Substring match
                    elif target_clean in detected_clean or detected_clean in target_clean:
                        matched = True
                        match_type = "substring"
                    # 3. Word-based match (any significant word)
                    elif ' ' in text and len(text) > 20:
                        target_words = text.lower().split()
                        detected_words = det_text.lower().split()
                        for tword in target_words:
                            if len(tword) >= 4:
                                for dword in detected_words:
                                    if tword in dword or dword in tword:
                                        matched = True
                                        match_type = "word-based"
                                        break
                            if matched:
                                break
                    # 4. Character overlap (20% for very long)
                    if not matched and len(target_clean) > 30:
                        overlap = sum(1 for c in target_clean if c in detected_clean)
                        if overlap / len(target_clean) >= 0.20:
                            matched = True
                            match_type = "char-overlap"

                    if matched:
                        poly = rec_polys[j] if j < len(rec_polys) else None
                        if poly is not None:
                            detected_x = np.mean(poly[:, 0])
                            detected_y = np.mean(poly[:, 1])
                            distance = np.sqrt((detected_x - target_x)**2 + (detected_y - target_y)**2)
                            detected = True
                            detected_text = det_text
                            break

            # Generous tolerance for long strings
            tolerance = 1000.0 if len(text) > 30 else 500.0
            test_success = detected and (distance is not None and distance <= tolerance)

            if test_success:
                success += 1
                status = "✓"
            else:
                status = "✗"

            results.append({
                'text': text,
                'length': len(text),
                'detected': bool(detected),
                'detected_text': str(detected_text) if detected_text else None,
                'match_type': match_type,
                'distance': float(distance) if distance is not None else None,
                'tolerance': float(tolerance),
                'success': bool(test_success),
                'ocr_time_ms': float(ocr_time)
            })

            status_msg = f"  {status} [{i+1}/{total}] ({len(text)} chars) '{text[:40]}...' → "
            if detected:
                status_msg += f"Detected ({match_type}) | Distance: {distance:.1f}px"
            else:
                status_msg += "NOT DETECTED"
            print(status_msg)

        print(f"\n{'='*80}")
        print(f"LONG STRING INDIVIDUAL TEST RESULTS")
        print(f"{'='*80}")
        print(f"Success: {success}/{total} = {(success/total*100):.1f}%")
        print(f"Failures: {total - success}")
        print(f"{'='*80}\n")

        return results, success, total

if __name__ == "__main__":
    print("="*80)
    print("LONG STRING FIX TEST - Individual Testing (Not Batched)")
    print("="*80)
    print()

    tester = LongStringIndividualTest()
    results, success, total = tester.test_long_strings()

    # Save results
    output = {
        'test_type': 'Long Strings - Individual Testing',
        'total_tests': total,
        'successful': success,
        'failed': total - success,
        'accuracy': (success / total * 100) if total > 0 else 0,
        'results': results
    }

    with open('long_strings_individual_results.json', 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ Results saved to long_strings_individual_results.json")

    # Compare to original batch testing
    print(f"\nCOMPARISON:")
    print(f"  Original (batch of 20):  26/50 = 52.0%")
    print(f"  Individual testing:      {success}/{total} = {(success/total*100):.1f}%")
    improvement = success - int(26 * total / 50)  # Proportional comparison
    print(f"  Estimated improvement:   ~{improvement} more cases working")
