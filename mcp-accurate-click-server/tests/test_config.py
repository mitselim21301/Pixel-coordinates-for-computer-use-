"""
Unit Tests for Configuration and Persistence System
====================================================

Tests for ConfigManager, StateManager, and CalibrationStorage.
"""

import os
import sys
import json
import time
import tempfile
import shutil
from pathlib import Path

import pytest
import numpy as np
import yaml

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import (
    ConfigManager,
    StateManager,
    CalibrationStorage,
    CalibrationMetrics,
    OCRConfig,
    CalibrationConfig,
    ClickConfig,
    PerformanceConfig,
    LoggingConfig,
    ConfigurationError,
    create_default_config,
)


class TestOCRConfig:
    """Test OCRConfig dataclass"""

    def test_default_values(self):
        """Test default configuration values"""
        config = OCRConfig()
        assert config.language == "en"
        assert config.use_gpu is False
        assert config.confidence_threshold == 0.6
        assert config.multi_pass_enabled is True
        assert config.num_passes == 3

    def test_custom_values(self):
        """Test custom configuration values"""
        config = OCRConfig(
            language="zh",
            use_gpu=True,
            num_passes=5
        )
        assert config.language == "zh"
        assert config.use_gpu is True
        assert config.num_passes == 5


class TestCalibrationConfig:
    """Test CalibrationConfig dataclass"""

    def test_default_values(self):
        """Test default configuration values"""
        config = CalibrationConfig()
        assert config.num_points == 100
        assert config.regional_grid == (2, 2)
        assert config.use_subpixel_refinement is True
        assert config.auto_recalibrate_enabled is True

    def test_custom_values(self):
        """Test custom configuration values"""
        config = CalibrationConfig(
            num_points=200,
            regional_grid=(3, 3),
            pattern_type="random"
        )
        assert config.num_points == 200
        assert config.regional_grid == (3, 3)
        assert config.pattern_type == "random"


class TestConfigManager:
    """Test ConfigManager class"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_config_file(self, temp_dir):
        """Create sample configuration file"""
        config_path = Path(temp_dir) / "test_config.yaml"
        config_data = {
            'schema_version': '1.0.0',
            'ocr': {
                'language': 'en',
                'use_gpu': True,
                'confidence_threshold': 0.7,
            },
            'calibration': {
                'num_points': 150,
                'regional_grid': [2, 2],
            },
        }
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        return str(config_path)

    def test_default_initialization(self):
        """Test initialization with default values"""
        config = ConfigManager()
        assert config.ocr.language == "en"
        assert config.calibration.num_points == 100
        assert config.click.button == "left"

    def test_load_from_yaml(self, sample_config_file):
        """Test loading configuration from YAML file"""
        config = ConfigManager(config_path=sample_config_file)
        assert config.ocr.use_gpu is True
        assert config.ocr.confidence_threshold == 0.7
        assert config.calibration.num_points == 150

    def test_save_configuration(self, temp_dir):
        """Test saving configuration to file"""
        config = ConfigManager()
        config.ocr.use_gpu = True
        config.calibration.num_points = 200

        save_path = Path(temp_dir) / "saved_config.yaml"
        config.save(str(save_path))

        # Load and verify
        with open(save_path) as f:
            saved_data = yaml.safe_load(f)

        assert saved_data['ocr']['use_gpu'] is True
        assert saved_data['calibration']['num_points'] == 200

    def test_env_override_bool(self):
        """Test environment variable override for boolean"""
        os.environ['MCP_OCR_USE_GPU'] = 'true'
        config = ConfigManager()
        assert config.ocr.use_gpu is True

        os.environ['MCP_OCR_USE_GPU'] = 'false'
        config = ConfigManager()
        assert config.ocr.use_gpu is False

        del os.environ['MCP_OCR_USE_GPU']

    def test_env_override_int(self):
        """Test environment variable override for integer"""
        os.environ['MCP_CALIBRATION_POINTS'] = '250'
        config = ConfigManager()
        assert config.calibration.num_points == 250
        del os.environ['MCP_CALIBRATION_POINTS']

    def test_env_override_float(self):
        """Test environment variable override for float"""
        os.environ['MCP_OCR_CONFIDENCE_THRESHOLD'] = '0.8'
        config = ConfigManager()
        assert config.ocr.confidence_threshold == 0.8
        del os.environ['MCP_OCR_CONFIDENCE_THRESHOLD']

    def test_env_override_string(self):
        """Test environment variable override for string"""
        os.environ['MCP_LOG_LEVEL'] = 'DEBUG'
        config = ConfigManager()
        assert config.logging.level == 'DEBUG'
        del os.environ['MCP_LOG_LEVEL']

    def test_validation_confidence_threshold(self):
        """Test validation of confidence threshold"""
        config = ConfigManager()
        config.ocr.confidence_threshold = 1.5
        with pytest.raises(ConfigurationError):
            config._validate_config()

    def test_validation_num_points(self):
        """Test validation of calibration points"""
        config = ConfigManager()
        config.calibration.num_points = 2
        with pytest.raises(ConfigurationError):
            config._validate_config()

    def test_validation_click_button(self):
        """Test validation of click button"""
        config = ConfigManager()
        config.click.button = "invalid"
        with pytest.raises(ConfigurationError):
            config._validate_config()

    def test_get_dict(self):
        """Test getting configuration as dictionary"""
        config = ConfigManager()
        config_dict = config.get_dict()

        assert 'ocr' in config_dict
        assert 'calibration' in config_dict
        assert 'click' in config_dict
        assert config_dict['ocr']['language'] == 'en'


class TestStateManager:
    """Test StateManager class"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_initial_state(self, temp_dir):
        """Test initial state"""
        state = StateManager(state_dir=temp_dir)
        assert state.is_calibrated is False
        assert state.click_count == 0
        assert state.success_count == 0
        assert state.get_success_rate() == 0.0

    def test_set_calibrated(self, temp_dir):
        """Test setting calibrated state"""
        state = StateManager(state_dir=temp_dir)

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

        assert state.is_calibrated is True
        assert state.calibration_metrics is not None
        assert state.calibration_metrics.success_rate == 0.998

    def test_record_clicks(self, temp_dir):
        """Test recording click attempts"""
        state = StateManager(state_dir=temp_dir)

        # Record successful clicks
        for _ in range(10):
            state.record_click(success=True, error=0.5)

        assert state.click_count == 10
        assert state.success_count == 10
        assert state.get_success_rate() == 1.0

        # Record failed clicks
        for _ in range(5):
            state.record_click(success=False, error=5.0)

        assert state.click_count == 15
        assert state.success_count == 10
        assert abs(state.get_success_rate() - 0.667) < 0.01

    def test_needs_recalibration(self, temp_dir):
        """Test recalibration detection"""
        state = StateManager(state_dir=temp_dir)

        # Not calibrated -> needs calibration
        assert state.needs_recalibration() is True

        # Set calibrated
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

        # Good success rate -> no recalibration needed
        for _ in range(100):
            state.record_click(success=True, error=0.5)

        assert state.needs_recalibration(threshold=0.95) is False

        # Poor success rate -> needs recalibration
        for _ in range(100):
            state.record_click(success=False, error=5.0)

        assert state.needs_recalibration(threshold=0.95) is True

    def test_state_persistence(self, temp_dir):
        """Test state persistence across instances"""
        # Create first instance and record data
        state1 = StateManager(state_dir=temp_dir)
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
        state1.set_calibrated(metrics)

        for _ in range(50):
            state1.record_click(success=True, error=0.5)

        state1._save_state()

        # Create second instance and verify data persisted
        state2 = StateManager(state_dir=temp_dir)
        assert state2.is_calibrated is True
        assert state2.click_count == 50
        assert state2.success_count == 50

    def test_get_statistics(self, temp_dir):
        """Test getting comprehensive statistics"""
        state = StateManager(state_dir=temp_dir)

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

        for _ in range(100):
            state.record_click(success=True, error=0.5)

        stats = state.get_statistics()

        assert stats['is_calibrated'] is True
        assert stats['total_clicks'] == 100
        assert stats['successful_clicks'] == 100
        assert stats['overall_success_rate'] == 1.0


class TestCalibrationStorage:
    """Test CalibrationStorage class"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_save_and_load(self, temp_dir):
        """Test saving and loading calibration data"""
        storage = CalibrationStorage(storage_dir=temp_dir)

        # Create sample data
        regional_offsets = {
            (0, 0): np.array([3.2, -2.8]),
            (0, 1): np.array([3.5, -2.6]),
            (1, 0): np.array([3.1, -3.0]),
            (1, 1): np.array([3.4, -2.9]),
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

        # Save
        storage.save(regional_offsets, (2, 2), (1920, 1080), metrics)

        # Load
        loaded = storage.load()

        assert loaded is not None
        assert loaded['grid_size'] == (2, 2)
        assert loaded['screen_size'] == (1920, 1080)
        assert loaded['metrics'].success_rate == 0.998

        # Verify offsets
        for region, offset in regional_offsets.items():
            assert np.allclose(loaded['regional_offsets'][region], offset)

    def test_no_calibration_file(self, temp_dir):
        """Test loading when no calibration file exists"""
        storage = CalibrationStorage(storage_dir=temp_dir)
        loaded = storage.load()
        assert loaded is None

    def test_backup_creation(self, temp_dir):
        """Test automatic backup creation"""
        storage = CalibrationStorage(storage_dir=temp_dir)

        regional_offsets = {
            (0, 0): np.array([3.2, -2.8]),
            (0, 1): np.array([3.5, -2.6]),
            (1, 0): np.array([3.1, -3.0]),
            (1, 1): np.array([3.4, -2.9]),
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

        # Save first calibration
        storage.save(regional_offsets, (2, 2), (1920, 1080), metrics)

        # Save second calibration (should create backup of first)
        time.sleep(0.1)  # Ensure different timestamp
        storage.save(regional_offsets, (2, 2), (1920, 1080), metrics)

        # Check backup was created
        backups = storage.list_backups()
        assert len(backups) > 0

    def test_list_backups(self, temp_dir):
        """Test listing backup files"""
        storage = CalibrationStorage(storage_dir=temp_dir)

        regional_offsets = {
            (0, 0): np.array([3.2, -2.8]),
            (0, 1): np.array([3.5, -2.6]),
            (1, 0): np.array([3.1, -3.0]),
            (1, 1): np.array([3.4, -2.9]),
        }

        # Create multiple calibrations
        for i in range(3):
            metrics = CalibrationMetrics(
                timestamp=time.time(),
                num_points=100,
                mean_error=0.65 + i*0.1,
                median_error=0.61,
                max_error=2.08,
                std_error=0.35,
                success_rate=0.998 - i*0.01,
                regional_grid=(2, 2)
            )
            storage.save(regional_offsets, (2, 2), (1920, 1080), metrics)
            time.sleep(0.1)

        backups = storage.list_backups()
        assert len(backups) >= 2  # At least 2 backups

        # Verify backup info
        for backup in backups:
            assert 'file' in backup
            assert 'timestamp' in backup
            assert 'success_rate' in backup

    def test_restore_backup(self, temp_dir):
        """Test restoring from backup"""
        storage = CalibrationStorage(storage_dir=temp_dir)

        regional_offsets = {
            (0, 0): np.array([3.2, -2.8]),
            (0, 1): np.array([3.5, -2.6]),
            (1, 0): np.array([3.1, -3.0]),
            (1, 1): np.array([3.4, -2.9]),
        }

        # Save first calibration
        metrics1 = CalibrationMetrics(
            timestamp=time.time(),
            num_points=100,
            mean_error=0.65,
            median_error=0.61,
            max_error=2.08,
            std_error=0.35,
            success_rate=0.998,
            regional_grid=(2, 2)
        )
        storage.save(regional_offsets, (2, 2), (1920, 1080), metrics1)
        time.sleep(0.2)

        # Save second calibration
        metrics2 = CalibrationMetrics(
            timestamp=time.time(),
            num_points=100,
            mean_error=0.85,
            median_error=0.81,
            max_error=2.5,
            std_error=0.45,
            success_rate=0.95,
            regional_grid=(2, 2)
        )
        storage.save(regional_offsets, (2, 2), (1920, 1080), metrics2)

        # Current should be second calibration
        current = storage.load()
        assert current['metrics'].success_rate == 0.95

        # Restore first calibration
        backups = storage.list_backups()
        if backups:
            storage.restore_backup(backups[0]['file'])

            # Verify restoration
            restored = storage.load()
            assert restored['metrics'].success_rate == 0.998


class TestCreateDefaultConfig:
    """Test create_default_config function"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_create_default_config(self, temp_dir):
        """Test creating default configuration file"""
        config_path = Path(temp_dir) / "default_config.yaml"
        create_default_config(str(config_path))

        assert config_path.exists()

        # Load and verify
        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        assert 'ocr' in config_data
        assert 'calibration' in config_data
        assert config_data['calibration']['num_points'] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
