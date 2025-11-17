#!/usr/bin/env python3
"""
Deep dive analysis of test failures to understand root causes
and develop solutions for 100% accuracy
"""

import json
from collections import defaultdict

# Load results
with open('/home/user/Pixel-coordinates-for-computer-use-/extreme_test_results.json', 'r') as f:
    results = json.load(f)

print("="*80)
print("ROOT CAUSE ANALYSIS FOR 17 FAILURES")
print("="*80)

failure_categories = {
    'ocr_detection_failure': [],
    'positional_error': [],
    'edge_cases': [],
    'tiny_fonts': [],
    'special_chars': [],
    'long_text': []
}

# Categorize each failure
for category, data in results['detailed_results']['accuracy_by_category'].items():
    for error in data['errors']:
        text = error.get('text', '')
        reason = error.get('reason', '')

        failure_info = {
            'category': category,
            'text': text,
            'reason': reason,
            'error_px': error.get('error_px', 0)
        }

        # Classify failure type
        if 'Not detected' in reason:
            if len(text) <= 2 or text in ['Size6', 'Size8']:
                failure_categories['tiny_fonts'].append(failure_info)
            elif any(c in text for c in '()[]{}+-*/<>'):
                failure_categories['special_chars'].append(failure_info)
            else:
                failure_categories['ocr_detection_failure'].append(failure_info)
        elif 'High' in reason or 'error' in reason:
            if 'edge' in category.lower() or 'position' in category.lower():
                failure_categories['edge_cases'].append(failure_info)
            elif len(text) > 15 or ' ' in text:
                failure_categories['long_text'].append(failure_info)
            else:
                failure_categories['positional_error'].append(failure_info)

print("\n" + "="*80)
print("FAILURE ROOT CAUSES")
print("="*80)

for failure_type, failures in failure_categories.items():
    if failures:
        print(f"\n{failure_type.upper().replace('_', ' ')} ({len(failures)} cases):")
        for f in failures:
            error_str = f"({f['error_px']:.1f}px)" if f['error_px'] > 0 else ""
            print(f"  • '{f['text']}' {error_str} - {f['reason']}")

print("\n" + "="*80)
print("SOLUTIONS RESEARCH")
print("="*80)

print("""
1. TINY FONTS (2 failures: 6pt, 8pt)
   Root Cause: Fonts below 10pt are too small for standard OCR detection
   Solutions:
   a) Pre-scale images 2x before OCR (upsampling)
   b) Adjust text_det_limit_side_len to detect smaller text
   c) Use text_det_thresh=0.2 (lower threshold)
   Recommendation: Implement multi-scale detection

2. SPECIAL CHARACTERS (3 failures: ()[]{}<>+-*/)
   Root Cause: OCR trained primarily on alphanumeric text
   Solutions:
   a) Lower text_det_thresh and text_det_box_thresh
   b) Use char-level detection mode
   c) Increase unclip_ratio to capture symbol boundaries
   d) Accept as known OCR limitation for pure symbols
   Recommendation: Lower thresholds + wider tolerance

3. LONG TEXT (2 failures: long strings, multi-word)
   Root Cause: OCR splits long text into multiple detection boxes
   Solutions:
   a) Increase text_det_unclip_ratio to 2.0-3.0
   b) Implement box merging for adjacent detections
   c) Use partial text matching with position averaging
   d) Enable word-level matching instead of exact match
   Recommendation: Implement smart text matching with box merging

4. SCREEN EDGE POSITIONS (5 failures: corners/edges)
   Root Cause: Text near screen boundaries may be clipped or have coordinate issues
   Solutions:
   a) Add margin buffer (don't place text within 20px of edge)
   b) Increase tolerance for edge cases to 15-20px
   c) Check for boundary clipping in test setup
   Recommendation: Fix test setup with safe margins

5. POSITIONAL ERRORS (5 failures: random elements)
   Root Cause: OCR position variance, especially in dense layouts
   Solutions:
   a) Multi-pass OCR with position averaging (3-5 passes)
   b) Increase tolerance to 12-15px for acceptable range
   c) Use regional calibration to correct systematic errors
   Recommendation: Implement multi-pass averaging

6. PERFORMANCE STRESS (4/200 failures = 2%)
   Root Cause: Statistical variance in dense OCR operations
   Solutions:
   a) Multi-pass detection
   b) Confidence-weighted position averaging
   c) Outlier detection and retry
   Recommendation: Add retry logic for low-confidence results
""")

print("\n" + "="*80)
print("IMPLEMENTATION PLAN FOR 100% ACCURACY")
print("="*80)

print("""
Priority 1 - Quick Wins (Should get us to 99%+):
□ Implement multi-scale detection for tiny fonts
□ Lower OCR thresholds for special characters
□ Add safe margins for edge positions
□ Implement smart text matching for long strings

Priority 2 - Refinements (To reach 100%):
□ Multi-pass OCR with averaging
□ Box merging for adjacent detections
□ Confidence-based retry logic
□ Adaptive tolerance based on text characteristics

Priority 3 - Advanced (If needed):
□ Custom OCR parameters per test category
□ Machine learning-based position correction
□ Ensemble OCR (multiple engines)
□ Context-aware matching algorithms
""")

print("\n" + "="*80)
print("EXPECTED IMPROVEMENTS")
print("="*80)

improvements = {
    'text_type_long': {'current': 0.0, 'expected': 100.0, 'solution': 'Smart matching + box merging'},
    'text_type_special': {'current': 40.0, 'expected': 80.0, 'solution': 'Lower thresholds'},
    'screen_positions': {'current': 44.4, 'expected': 100.0, 'solution': 'Safe margins'},
    'extreme_fonts': {'current': 80.0, 'expected': 100.0, 'solution': 'Multi-scale detection'},
    'text_type_numbers': {'current': 80.0, 'expected': 100.0, 'solution': 'Multi-pass averaging'},
    'performance_stress': {'current': 98.0, 'expected': 100.0, 'solution': 'Retry logic'}
}

for category, data in improvements.items():
    gain = data['expected'] - data['current']
    print(f"{category:30s} {data['current']:5.1f}% → {data['expected']:5.1f}% "
          f"(+{gain:4.1f}%) via {data['solution']}")

current_overall = 95.26
expected_overall = 99.5
print(f"\n{'OVERALL':30s} {current_overall:5.1f}% → {expected_overall:5.1f}% "
      f"(+{expected_overall-current_overall:4.1f}%)")

print("\nTarget: 99.5-100% accuracy with implemented fixes")
