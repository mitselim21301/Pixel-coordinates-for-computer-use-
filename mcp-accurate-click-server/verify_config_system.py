#!/usr/bin/env python3
"""
Configuration System Verification Script
Verifies all components of the configuration system are working correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

print("="*70)
print("MCP Accurate Click Server - Configuration System Verification")
print("="*70)

# Test 1: Import all modules
print("\n1. Testing module imports...")
try:
    from config import (
        ConfigManager,
        StateManager,
        CalibrationStorage,
        OCRConfig,
        CalibrationConfig,
        ClickConfig,
        PerformanceConfig,
        LoggingConfig,
        CalibrationMetrics,
        ConfigurationError,
    )
    print("   ✓ All modules imported successfully")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Load configuration
print("\n2. Testing configuration loading...")
try:
    config = ConfigManager()
    print(f"   ✓ Configuration loaded")
    print(f"     - OCR: {config.ocr.num_passes} passes, GPU={config.ocr.use_gpu}")
    print(f"     - Calibration: {config.calibration.num_points} points, {config.calibration.regional_grid} grid")
    print(f"     - Click: {config.click.button} button, validation={config.click.validate_click}")
except Exception as e:
    print(f"   ✗ Configuration loading failed: {e}")
    sys.exit(1)

# Test 3: StateManager
print("\n3. Testing StateManager...")
try:
    state = StateManager(state_dir="/tmp/mcp-verify-test")
    print(f"   ✓ StateManager initialized")
    print(f"     - Calibrated: {state.is_calibrated}")
    print(f"     - Click count: {state.click_count}")
except Exception as e:
    print(f"   ✗ StateManager failed: {e}")
    sys.exit(1)

# Test 4: CalibrationStorage
print("\n4. Testing CalibrationStorage...")
try:
    storage = CalibrationStorage(storage_dir="/tmp/mcp-verify-test")
    print(f"   ✓ CalibrationStorage initialized")
except Exception as e:
    print(f"   ✗ CalibrationStorage failed: {e}")
    sys.exit(1)

# Test 5: Validation
print("\n5. Testing configuration validation...")
try:
    config = ConfigManager()
    config._validate_config()
    print(f"   ✓ Configuration validation passed")
except Exception as e:
    print(f"   ✗ Validation failed: {e}")
    sys.exit(1)

# Test 6: Dataclasses
print("\n6. Testing configuration dataclasses...")
try:
    ocr_config = OCRConfig()
    cal_config = CalibrationConfig()
    click_config = ClickConfig()
    perf_config = PerformanceConfig()
    log_config = LoggingConfig()
    print(f"   ✓ All dataclasses instantiated")
except Exception as e:
    print(f"   ✗ Dataclass creation failed: {e}")
    sys.exit(1)

# Test 7: Check files exist
print("\n7. Checking configuration files...")
files_to_check = [
    ('src/config.py', 'Main config module'),
    ('config.yaml', 'Default configuration'),
    ('.env.example', 'Environment template'),
    ('CONFIG_README.md', 'Documentation'),
    ('examples/config_example.py', 'Examples'),
    ('tests/test_config.py', 'Tests'),
]

all_exist = True
for filepath, description in files_to_check:
    if os.path.exists(filepath):
        size_kb = os.path.getsize(filepath) / 1024
        print(f"   ✓ {description}: {filepath} ({size_kb:.1f} KB)")
    else:
        print(f"   ✗ Missing: {filepath}")
        all_exist = False

if not all_exist:
    sys.exit(1)

# Summary
print("\n" + "="*70)
print("VERIFICATION COMPLETE: ✓ All tests passed!")
print("="*70)
print("\nConfiguration system is ready for use.")
print("\nQuick start:")
print("  from src.config import ConfigManager, StateManager, CalibrationStorage")
print("  config = ConfigManager()")
print("\nDocumentation:")
print("  - CONFIG_README.md - Full documentation")
print("  - QUICK_START_CONFIG.md - Quick reference")
print("  - examples/config_example.py - Working examples")
print("="*70 + "\n")
