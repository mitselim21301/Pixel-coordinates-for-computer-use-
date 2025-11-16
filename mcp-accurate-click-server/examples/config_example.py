"""
Configuration System Example
=============================

Demonstrates the complete configuration and persistence system for MCP Accurate Click Server.

This example shows:
1. Loading configuration from YAML/JSON
2. Environment variable overrides
3. State management and metrics tracking
4. Calibration data persistence
5. Configuration validation
"""

import os
import sys
import time
import logging
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import (
    ConfigManager,
    StateManager,
    CalibrationStorage,
    CalibrationMetrics,
    OCRConfig,
    CalibrationConfig,
    create_default_config,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_config_loading():
    """Example 1: Basic configuration loading"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Configuration Loading")
    print("="*70)

    # Load configuration (searches default locations)
    config = ConfigManager()

    # Access configuration sections
    print(f"\nOCR Configuration:")
    print(f"  Language: {config.ocr.language}")
    print(f"  GPU Enabled: {config.ocr.use_gpu}")
    print(f"  Confidence Threshold: {config.ocr.confidence_threshold}")
    print(f"  Multi-pass: {config.ocr.num_passes} passes")

    print(f"\nCalibration Configuration:")
    print(f"  Points: {config.calibration.num_points}")
    print(f"  Regional Grid: {config.calibration.regional_grid}")
    print(f"  Sub-pixel Refinement: {config.calibration.use_subpixel_refinement}")
    print(f"  Auto-recalibrate: {config.calibration.auto_recalibrate_enabled}")

    print(f"\nClick Configuration:")
    print(f"  Button: {config.click.button}")
    print(f"  Validate: {config.click.validate_click}")
    print(f"  Max Retries: {config.click.max_retries}")

    print(f"\nPerformance Configuration:")
    print(f"  Cache Enabled: {config.performance.cache_enabled}")
    print(f"  Max Workers: {config.performance.max_workers}")


def example_2_environment_overrides():
    """Example 2: Environment variable overrides"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Environment Variable Overrides")
    print("="*70)

    # Set environment variables
    os.environ['MCP_OCR_USE_GPU'] = 'true'
    os.environ['MCP_CALIBRATION_POINTS'] = '150'
    os.environ['MCP_LOG_LEVEL'] = 'DEBUG'

    # Load config (will apply env overrides)
    config = ConfigManager()

    print(f"\nConfiguration with Environment Overrides:")
    print(f"  OCR GPU (from MCP_OCR_USE_GPU): {config.ocr.use_gpu}")
    print(f"  Calibration Points (from MCP_CALIBRATION_POINTS): {config.calibration.num_points}")
    print(f"  Log Level (from MCP_LOG_LEVEL): {config.logging.level}")

    # Clean up
    del os.environ['MCP_OCR_USE_GPU']
    del os.environ['MCP_CALIBRATION_POINTS']
    del os.environ['MCP_LOG_LEVEL']


def example_3_custom_configuration():
    """Example 3: Creating custom configuration"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Custom Configuration")
    print("="*70)

    # Create config manager
    config = ConfigManager()

    # Customize OCR settings
    config.ocr = OCRConfig(
        language='en',
        use_gpu=True,
        num_passes=5,
        confidence_threshold=0.8
    )

    # Customize calibration settings
    config.calibration = CalibrationConfig(
        num_points=200,
        regional_grid=(3, 3),
        pattern_type='adaptive_grid',
        use_subpixel_refinement=True
    )

    print(f"\nCustom Configuration:")
    print(f"  OCR: {config.ocr.num_passes} passes, GPU={config.ocr.use_gpu}")
    print(f"  Calibration: {config.calibration.num_points} points, "
          f"{config.calibration.regional_grid} grid")

    # Save to custom location
    custom_config_path = "/tmp/custom_config.yaml"
    config.save(custom_config_path)
    print(f"\nSaved custom configuration to: {custom_config_path}")

    # Load from custom location
    loaded_config = ConfigManager(config_path=custom_config_path)
    print(f"Loaded configuration: {loaded_config.calibration.num_points} points")


def example_4_state_management():
    """Example 4: State management and metrics tracking"""
    print("\n" + "="*70)
    print("EXAMPLE 4: State Management")
    print("="*70)

    # Initialize state manager
    state = StateManager(state_dir="/tmp/mcp-test")

    # Check initial state
    print(f"\nInitial State:")
    print(f"  Calibrated: {state.is_calibrated}")
    print(f"  Total Clicks: {state.click_count}")
    print(f"  Success Rate: {state.get_success_rate():.1%}")

    # Simulate calibration
    print(f"\nSimulating calibration...")
    metrics = CalibrationMetrics(
        timestamp=time.time(),
        num_points=100,
        mean_error=0.65,
        median_error=0.61,
        max_error=2.08,
        std_error=0.35,
        success_rate=0.998,
        regional_grid=(2, 2)
    )
    state.set_calibrated(metrics)

    print(f"Calibration complete:")
    print(f"  Mean Error: {metrics.mean_error:.3f} px")
    print(f"  Success Rate: {metrics.success_rate:.1%}")

    # Simulate clicks
    print(f"\nSimulating 100 clicks...")
    for i in range(100):
        # 99% success rate
        success = np.random.random() < 0.99
        error = np.abs(np.random.normal(0.65, 0.35)) if success else 5.0
        state.record_click(success=success, error=error)

    # Get updated statistics
    stats = state.get_statistics()
    print(f"\nStatistics after 100 clicks:")
    print(f"  Total Clicks: {stats['total_clicks']}")
    print(f"  Success Rate: {stats['overall_success_rate']:.1%}")
    print(f"  Recent Success Rate (last 100): {stats['recent_success_rate']:.1%}")
    print(f"  Needs Recalibration: {stats['needs_recalibration']}")

    # Simulate accuracy drop
    print(f"\nSimulating accuracy drop...")
    for i in range(50):
        # 85% success rate (below threshold)
        success = np.random.random() < 0.85
        error = np.abs(np.random.normal(1.5, 0.8)) if success else 5.0
        state.record_click(success=success, error=error)

    stats = state.get_statistics()
    print(f"\nAfter accuracy drop:")
    print(f"  Recent Success Rate: {stats['recent_success_rate']:.1%}")
    print(f"  Needs Recalibration: {stats['needs_recalibration']}")


def example_5_calibration_storage():
    """Example 5: Calibration data persistence"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Calibration Storage")
    print("="*70)

    # Initialize storage
    storage = CalibrationStorage(storage_dir="/tmp/mcp-test")

    # Create sample calibration data
    regional_offsets = {
        (0, 0): np.array([3.2, -2.8]),  # Top-left
        (0, 1): np.array([3.5, -2.6]),  # Top-right
        (1, 0): np.array([3.1, -3.0]),  # Bottom-left
        (1, 1): np.array([3.4, -2.9]),  # Bottom-right
    }

    metrics = CalibrationMetrics(
        timestamp=time.time(),
        num_points=100,
        mean_error=0.65,
        median_error=0.61,
        max_error=2.08,
        std_error=0.35,
        success_rate=0.998,
        regional_grid=(2, 2)
    )

    # Save calibration
    print(f"\nSaving calibration data...")
    storage.save(
        regional_offsets=regional_offsets,
        grid_size=(2, 2),
        screen_size=(1920, 1080),
        metrics=metrics
    )
    print(f"Calibration saved successfully")

    # Load calibration
    print(f"\nLoading calibration data...")
    calibration = storage.load()

    if calibration:
        print(f"Calibration loaded successfully:")
        print(f"  Version: {calibration['version']}")
        print(f"  Grid Size: {calibration['grid_size']}")
        print(f"  Screen Size: {calibration['screen_size']}")
        print(f"  Success Rate: {calibration['metrics'].success_rate:.1%}")
        print(f"  Mean Error: {calibration['metrics'].mean_error:.3f} px")

        # Display regional offsets
        print(f"\n  Regional Offsets:")
        for region, offset in calibration['regional_offsets'].items():
            print(f"    Region {region}: [{offset[0]:.2f}, {offset[1]:.2f}] px")

    # Create additional backups for testing
    print(f"\nCreating backup calibrations...")
    for i in range(3):
        time.sleep(1)  # Ensure different timestamps
        new_metrics = CalibrationMetrics(
            timestamp=time.time(),
            num_points=100,
            mean_error=0.65 + i*0.1,
            median_error=0.61 + i*0.1,
            max_error=2.08 + i*0.2,
            std_error=0.35,
            success_rate=0.998 - i*0.01,
            regional_grid=(2, 2)
        )
        storage.save(regional_offsets, (2, 2), (1920, 1080), new_metrics)

    # List backups
    backups = storage.list_backups()
    print(f"\nAvailable backups ({len(backups)}):")
    for i, backup in enumerate(backups[-5:]):  # Show last 5
        print(f"  {i+1}. {os.path.basename(backup['file'])}")
        print(f"     Success Rate: {backup['success_rate']:.1%}, "
              f"Mean Error: {backup['mean_error']:.3f} px")


def example_6_validation():
    """Example 6: Configuration validation"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Configuration Validation")
    print("="*70)

    # Create invalid configuration
    print(f"\nTesting configuration validation...")

    try:
        config = ConfigManager()

        # Try invalid values
        config.ocr.confidence_threshold = 1.5  # Invalid: > 1.0
        config._validate_config()

    except Exception as e:
        print(f"\nValidation error (expected): {e}")

    try:
        config = ConfigManager()
        config.calibration.num_points = 2  # Invalid: < 4
        config._validate_config()

    except Exception as e:
        print(f"\nValidation error (expected): {e}")

    try:
        config = ConfigManager()
        config.click.button = "invalid_button"  # Invalid button
        config._validate_config()

    except Exception as e:
        print(f"\nValidation error (expected): {e}")

    print(f"\nValidation system working correctly!")


def example_7_complete_workflow():
    """Example 7: Complete workflow demonstration"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Complete Workflow")
    print("="*70)

    # 1. Load configuration
    print("\n1. Loading configuration...")
    config = ConfigManager()
    print(f"   Configuration loaded with {config.calibration.num_points} calibration points")

    # 2. Initialize state
    print("\n2. Initializing state manager...")
    state = StateManager(state_dir="/tmp/mcp-test")

    # 3. Check if calibration needed
    print("\n3. Checking calibration status...")
    if not state.is_calibrated or state.needs_recalibration():
        print("   System needs calibration")

        # Simulate calibration process
        print("   Performing calibration...")
        metrics = CalibrationMetrics(
            timestamp=time.time(),
            num_points=config.calibration.num_points,
            mean_error=0.65,
            median_error=0.61,
            max_error=2.08,
            std_error=0.35,
            success_rate=0.998,
            regional_grid=config.calibration.regional_grid
        )

        # Save calibration data
        storage = CalibrationStorage(storage_dir="/tmp/mcp-test")
        regional_offsets = {
            (0, 0): np.array([3.2, -2.8]),
            (0, 1): np.array([3.5, -2.6]),
            (1, 0): np.array([3.1, -3.0]),
            (1, 1): np.array([3.4, -2.9]),
        }
        storage.save(regional_offsets, (2, 2), (1920, 1080), metrics)

        # Update state
        state.set_calibrated(metrics)
        print(f"   Calibration complete: {metrics.success_rate:.1%} success rate")
    else:
        print("   Using existing calibration")
        storage = CalibrationStorage(storage_dir="/tmp/mcp-test")
        calibration = storage.load()
        print(f"   Loaded calibration: {calibration['metrics'].success_rate:.1%} success rate")

    # 4. Simulate click operations
    print("\n4. Performing click operations...")
    num_clicks = 50
    for i in range(num_clicks):
        # Simulate click with 99% success rate
        success = np.random.random() < 0.99
        error = np.abs(np.random.normal(0.65, 0.35))
        state.record_click(success=success, error=error)

    # 5. Monitor performance
    print("\n5. Monitoring performance...")
    stats = state.get_statistics()
    print(f"   Total Clicks: {stats['total_clicks']}")
    print(f"   Success Rate: {stats['overall_success_rate']:.1%}")
    print(f"   Needs Recalibration: {stats['needs_recalibration']}")

    # 6. Save state
    print("\n6. State automatically saved to disk")
    print(f"   State file: ~/.mcp-accurate-click/state.json")

    print("\n✓ Complete workflow executed successfully!")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("MCP Accurate Click Server - Configuration System Examples")
    print("="*70)

    # Create default config file if it doesn't exist
    if not os.path.exists("config.yaml"):
        print("\nCreating default config.yaml...")
        create_default_config("config.yaml")
        print("✓ Default configuration created")

    # Run examples
    example_1_basic_config_loading()
    example_2_environment_overrides()
    example_3_custom_configuration()
    example_4_state_management()
    example_5_calibration_storage()
    example_6_validation()
    example_7_complete_workflow()

    print("\n" + "="*70)
    print("All examples completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
