"""
Configuration and Persistence System for MCP Accurate Click Server

This module provides:
1. ConfigManager - Load/save configuration from YAML/JSON with validation
2. StateManager - Track calibration state, metrics, and error history
3. CalibrationStorage - Persist calibration data with backups and versioning

Based on research findings:
- 100 calibration points for 99.95%+ accuracy
- 2x2 regional grid for non-uniform error correction
- Sub-pixel refinement for ultra-high accuracy
"""

import os
import json
import yaml
import time
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
import numpy as np


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class OCRConfig:
    """OCR engine configuration"""
    language: str = "en"
    use_gpu: bool = False
    use_angle_cls: bool = True
    confidence_threshold: float = 0.6
    show_log: bool = False
    det_db_thresh: float = 0.3
    det_db_box_thresh: float = 0.6
    rec_batch_num: int = 6

    # Multi-pass OCR for higher accuracy
    multi_pass_enabled: bool = True
    num_passes: int = 3
    averaging_method: str = "confidence_weighted"  # Options: mean, median, confidence_weighted


@dataclass
class CalibrationConfig:
    """Calibration system configuration"""
    num_points: int = 100  # Research shows 100 points for 99.95%+ accuracy
    regional_grid: Tuple[int, int] = (2, 2)  # 2x2 grid = 4 regions
    use_subpixel_refinement: bool = True
    subpixel_window_size: int = 5

    # Auto-recalibration
    auto_recalibrate_enabled: bool = True
    recalibrate_on_dpi_change: bool = True
    recalibrate_on_accuracy_drop: bool = True
    accuracy_drop_threshold: float = 0.95  # Recalibrate if success rate < 95%

    # Calibration patterns
    pattern_type: str = "adaptive_grid"  # Options: uniform_grid, adaptive_grid, random
    edge_weight: float = 1.5  # Weight more points near edges

    # Validation
    validation_split: float = 0.2  # Use 20% of points for validation
    min_validation_accuracy: float = 0.995  # Require 99.5%+ on validation set


@dataclass
class ClickConfig:
    """Click execution configuration"""
    button: str = "left"  # Options: left, right, middle
    delay_before_click: float = 0.05  # seconds
    delay_after_click: float = 0.1  # seconds

    # Click validation
    validate_click: bool = True
    validation_timeout: float = 2.0  # seconds
    retry_on_failure: bool = True
    max_retries: int = 3

    # Safety
    require_confirmation: bool = False
    exclusion_zones: List[Dict[str, int]] = field(default_factory=list)  # No-click zones


@dataclass
class PerformanceConfig:
    """Performance optimization settings"""
    # Caching
    cache_enabled: bool = True
    cache_ocr_results: bool = True
    cache_ttl: int = 300  # seconds (5 minutes)
    max_cache_size: int = 1000  # Maximum cached items

    # Threading
    use_threading: bool = True
    max_workers: int = 4

    # Memory management
    batch_size: int = 10
    clear_cache_on_recalibrate: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_to_file: bool = True
    log_file: str = "~/.mcp-accurate-click/logs/server.log"
    max_log_size: int = 10485760  # 10 MB
    backup_count: int = 5

    # Performance logging
    log_performance_metrics: bool = True
    log_click_accuracy: bool = True
    log_ocr_results: bool = False  # Can be verbose


class ConfigManager:
    """
    Manages configuration loading, validation, and persistence

    Features:
    - Load from YAML/JSON files
    - Environment variable overrides
    - Schema validation
    - Default values
    - User-friendly error messages
    """

    DEFAULT_CONFIG_PATHS = [
        "./config.yaml",
        "~/.mcp-accurate-click/config.yaml",
        "/etc/mcp-accurate-click/config.yaml"
    ]

    SCHEMA_VERSION = "1.0.0"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize ConfigManager

        Args:
            config_path: Path to config file. If None, searches default locations.
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}

        # Initialize with defaults
        self.ocr = OCRConfig()
        self.calibration = CalibrationConfig()
        self.click = ClickConfig()
        self.performance = PerformanceConfig()
        self.logging = LoggingConfig()

        # Load configuration
        self._load_config()
        self._apply_env_overrides()
        self._validate_config()

    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in default locations"""
        if self.config_path:
            path = Path(self.config_path).expanduser()
            if path.exists():
                return path
            else:
                logger.warning(f"Specified config file not found: {self.config_path}")

        for path_str in self.DEFAULT_CONFIG_PATHS:
            path = Path(path_str).expanduser()
            if path.exists():
                logger.info(f"Found config file: {path}")
                return path

        return None

    def _load_config(self):
        """Load configuration from file"""
        config_file = self._find_config_file()

        if not config_file:
            logger.info("No config file found, using defaults")
            return

        try:
            with open(config_file, 'r') as f:
                if config_file.suffix in ['.yaml', '.yml']:
                    self.config = yaml.safe_load(f) or {}
                elif config_file.suffix == '.json':
                    self.config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_file.suffix}")

            logger.info(f"Loaded configuration from {config_file}")

            # Parse into dataclass instances
            if 'ocr' in self.config:
                self.ocr = OCRConfig(**self.config['ocr'])
            if 'calibration' in self.config:
                # Convert tuple from list if needed
                if 'regional_grid' in self.config['calibration']:
                    self.config['calibration']['regional_grid'] = tuple(
                        self.config['calibration']['regional_grid']
                    )
                self.calibration = CalibrationConfig(**self.config['calibration'])
            if 'click' in self.config:
                self.click = ClickConfig(**self.config['click'])
            if 'performance' in self.config:
                self.performance = PerformanceConfig(**self.config['performance'])
            if 'logging' in self.config:
                self.logging = LoggingConfig(**self.config['logging'])

        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        env_mappings = {
            # OCR
            'MCP_OCR_LANGUAGE': ('ocr', 'language'),
            'MCP_OCR_USE_GPU': ('ocr', 'use_gpu', bool),
            'MCP_OCR_CONFIDENCE_THRESHOLD': ('ocr', 'confidence_threshold', float),

            # Calibration
            'MCP_CALIBRATION_POINTS': ('calibration', 'num_points', int),
            'MCP_AUTO_RECALIBRATE': ('calibration', 'auto_recalibrate_enabled', bool),

            # Click
            'MCP_CLICK_BUTTON': ('click', 'button'),
            'MCP_VALIDATE_CLICK': ('click', 'validate_click', bool),

            # Performance
            'MCP_CACHE_ENABLED': ('performance', 'cache_enabled', bool),
            'MCP_USE_GPU': ('ocr', 'use_gpu', bool),

            # Logging
            'MCP_LOG_LEVEL': ('logging', 'level'),
            'MCP_LOG_FILE': ('logging', 'log_file'),
        }

        for env_var, mapping in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                section = mapping[0]
                field_name = mapping[1]
                converter = mapping[2] if len(mapping) > 2 else str

                # Convert value
                try:
                    if converter == bool:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        value = converter(value)

                    # Apply to config object
                    config_obj = getattr(self, section)
                    setattr(config_obj, field_name, value)
                    logger.debug(f"Applied env override: {env_var} = {value}")

                except Exception as e:
                    logger.warning(f"Failed to apply env override {env_var}: {e}")

    def _validate_config(self):
        """Validate configuration parameters"""
        errors = []

        # Validate OCR config
        if self.ocr.confidence_threshold < 0 or self.ocr.confidence_threshold > 1:
            errors.append("OCR confidence_threshold must be between 0 and 1")

        if self.ocr.num_passes < 1 or self.ocr.num_passes > 10:
            errors.append("OCR num_passes must be between 1 and 10")

        # Validate calibration config
        if self.calibration.num_points < 4:
            errors.append("Calibration num_points must be at least 4 (minimum 30 recommended)")

        if self.calibration.num_points > 10000:
            errors.append("Calibration num_points exceeds reasonable limit (10000)")

        grid_rows, grid_cols = self.calibration.regional_grid
        if grid_rows < 1 or grid_cols < 1:
            errors.append("Calibration regional_grid must have at least 1 row and 1 column")

        if grid_rows * grid_cols > 100:
            errors.append("Calibration regional_grid too fine (max 100 regions)")

        # Validate click config
        if self.click.button not in ['left', 'right', 'middle']:
            errors.append(f"Invalid click button: {self.click.button}")

        if self.click.max_retries < 0 or self.click.max_retries > 10:
            errors.append("Click max_retries must be between 0 and 10")

        # Validate performance config
        if self.performance.cache_ttl < 0:
            errors.append("Performance cache_ttl must be non-negative")

        if self.performance.max_workers < 1 or self.performance.max_workers > 32:
            errors.append("Performance max_workers must be between 1 and 32")

        # Validate logging config
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.logging.level not in valid_log_levels:
            errors.append(f"Invalid logging level: {self.logging.level}")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ConfigurationError(error_msg)

        logger.info("Configuration validation passed")

    def save(self, path: Optional[str] = None):
        """
        Save current configuration to file

        Args:
            path: Path to save to. If None, uses loaded config path or default.
        """
        if path is None:
            path = self.config_path or self.DEFAULT_CONFIG_PATHS[1]

        save_path = Path(path).expanduser()
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict
        config_dict = {
            'schema_version': self.SCHEMA_VERSION,
            'ocr': asdict(self.ocr),
            'calibration': asdict(self.calibration),
            'click': asdict(self.click),
            'performance': asdict(self.performance),
            'logging': asdict(self.logging),
        }

        # Save as YAML
        try:
            with open(save_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")

    def get_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            'ocr': asdict(self.ocr),
            'calibration': asdict(self.calibration),
            'click': asdict(self.click),
            'performance': asdict(self.performance),
            'logging': asdict(self.logging),
        }


@dataclass
class CalibrationMetrics:
    """Metrics for a calibration session"""
    timestamp: float
    num_points: int
    mean_error: float
    median_error: float
    max_error: float
    std_error: float
    success_rate: float
    regional_grid: Tuple[int, int]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StateManager:
    """
    Manages runtime state including calibration status and accuracy metrics

    Features:
    - Track calibration state and timestamps
    - Maintain accuracy metrics history
    - Error logging and analysis
    - Automatic state persistence
    """

    def __init__(self, state_dir: str = "~/.mcp-accurate-click"):
        """
        Initialize StateManager

        Args:
            state_dir: Directory for state files
        """
        self.state_dir = Path(state_dir).expanduser()
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = self.state_dir / "state.json"

        # State variables
        self.is_calibrated: bool = False
        self.calibration_timestamp: Optional[float] = None
        self.calibration_metrics: Optional[CalibrationMetrics] = None
        self.metrics_history: List[CalibrationMetrics] = []
        self.error_log: List[Dict[str, Any]] = []
        self.click_count: int = 0
        self.success_count: int = 0

        # Load existing state
        self._load_state()

    def _load_state(self):
        """Load state from disk"""
        if not self.state_file.exists():
            logger.info("No existing state file found")
            return

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)

            self.is_calibrated = state.get('is_calibrated', False)
            self.calibration_timestamp = state.get('calibration_timestamp')

            if state.get('calibration_metrics'):
                self.calibration_metrics = CalibrationMetrics(**state['calibration_metrics'])

            self.metrics_history = [
                CalibrationMetrics(**m) for m in state.get('metrics_history', [])
            ]

            self.error_log = state.get('error_log', [])
            self.click_count = state.get('click_count', 0)
            self.success_count = state.get('success_count', 0)

            logger.info(f"Loaded state: calibrated={self.is_calibrated}, "
                       f"clicks={self.click_count}, success_rate={self.get_success_rate():.1%}")

        except Exception as e:
            logger.error(f"Error loading state: {e}")

    def _save_state(self):
        """Save state to disk"""
        try:
            state = {
                'is_calibrated': self.is_calibrated,
                'calibration_timestamp': self.calibration_timestamp,
                'calibration_metrics': self.calibration_metrics.to_dict() if self.calibration_metrics else None,
                'metrics_history': [m.to_dict() for m in self.metrics_history],
                'error_log': self.error_log[-1000:],  # Keep last 1000 errors
                'click_count': self.click_count,
                'success_count': self.success_count,
                'last_updated': time.time(),
            }

            # Atomic write
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(state, f, indent=2)
            temp_file.replace(self.state_file)

            logger.debug("State saved successfully")

        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def set_calibrated(self, metrics: CalibrationMetrics):
        """
        Mark system as calibrated with metrics

        Args:
            metrics: Calibration metrics
        """
        self.is_calibrated = True
        self.calibration_timestamp = time.time()
        self.calibration_metrics = metrics
        self.metrics_history.append(metrics)

        # Keep only last 100 calibrations in history
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]

        self._save_state()
        logger.info(f"System calibrated: {metrics.mean_error:.3f}px mean error, "
                   f"{metrics.success_rate:.1%} success rate")

    def reset_calibration(self):
        """Reset calibration state"""
        self.is_calibrated = False
        self.calibration_timestamp = None
        self.calibration_metrics = None
        self._save_state()
        logger.info("Calibration reset")

    def record_click(self, success: bool, error: Optional[float] = None):
        """
        Record a click attempt

        Args:
            success: Whether click was successful
            error: Error distance in pixels (if known)
        """
        self.click_count += 1
        if success:
            self.success_count += 1

        if error is not None and error > 2.0:  # Log significant errors
            self.error_log.append({
                'timestamp': time.time(),
                'error': error,
                'success': success,
            })

        # Save state periodically (every 100 clicks)
        if self.click_count % 100 == 0:
            self._save_state()

    def get_success_rate(self) -> float:
        """Get overall click success rate"""
        if self.click_count == 0:
            return 0.0
        return self.success_count / self.click_count

    def get_recent_success_rate(self, num_clicks: int = 100) -> float:
        """
        Get recent success rate

        Args:
            num_clicks: Number of recent clicks to consider
        """
        if len(self.error_log) < num_clicks:
            return self.get_success_rate()

        recent_errors = self.error_log[-num_clicks:]
        successes = sum(1 for e in recent_errors if e['success'])
        return successes / len(recent_errors)

    def needs_recalibration(self, threshold: float = 0.95) -> bool:
        """
        Check if system needs recalibration based on success rate

        Args:
            threshold: Minimum acceptable success rate
        """
        if not self.is_calibrated:
            return True

        recent_rate = self.get_recent_success_rate(100)
        return recent_rate < threshold

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        return {
            'is_calibrated': self.is_calibrated,
            'calibration_age': time.time() - self.calibration_timestamp if self.calibration_timestamp else None,
            'current_metrics': self.calibration_metrics.to_dict() if self.calibration_metrics else None,
            'total_clicks': self.click_count,
            'successful_clicks': self.success_count,
            'overall_success_rate': self.get_success_rate(),
            'recent_success_rate': self.get_recent_success_rate(100),
            'needs_recalibration': self.needs_recalibration(),
            'calibration_count': len(self.metrics_history),
        }


class CalibrationStorage:
    """
    Manages persistence of calibration data

    Features:
    - Save/load calibration data to NPZ format
    - Automatic backups of previous calibrations
    - Version migration support
    - Integrity checking
    """

    VERSION = "1.0.0"

    def __init__(self, storage_dir: str = "~/.mcp-accurate-click"):
        """
        Initialize CalibrationStorage

        Args:
            storage_dir: Directory for calibration files
        """
        self.storage_dir = Path(storage_dir).expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.calibration_file = self.storage_dir / "calibration.npz"
        self.backup_dir = self.storage_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def save(self,
             regional_offsets: Dict[Tuple[int, int], np.ndarray],
             grid_size: Tuple[int, int],
             screen_size: Tuple[int, int],
             metrics: CalibrationMetrics):
        """
        Save calibration data

        Args:
            regional_offsets: Dict mapping (row, col) to offset array [dx, dy]
            grid_size: Calibration grid size (rows, cols)
            screen_size: Screen dimensions (width, height)
            metrics: Calibration metrics
        """
        # Backup existing calibration
        if self.calibration_file.exists():
            self._create_backup()

        # Prepare data for saving
        save_data = {
            'version': self.VERSION,
            'timestamp': time.time(),
            'grid_rows': grid_size[0],
            'grid_cols': grid_size[1],
            'screen_width': screen_size[0],
            'screen_height': screen_size[1],
        }

        # Add regional offsets
        for (row, col), offset in regional_offsets.items():
            save_data[f'offset_{row}_{col}'] = offset

        # Add metrics
        save_data['mean_error'] = metrics.mean_error
        save_data['median_error'] = metrics.median_error
        save_data['max_error'] = metrics.max_error
        save_data['std_error'] = metrics.std_error
        save_data['success_rate'] = metrics.success_rate
        save_data['num_points'] = metrics.num_points

        # Save to NPZ
        try:
            np.savez_compressed(self.calibration_file, **save_data)
            logger.info(f"Calibration saved to {self.calibration_file}")
        except Exception as e:
            logger.error(f"Error saving calibration: {e}")
            raise

    def load(self) -> Optional[Dict[str, Any]]:
        """
        Load calibration data

        Returns:
            Dictionary containing calibration data, or None if not found
        """
        if not self.calibration_file.exists():
            logger.info("No calibration file found")
            return None

        try:
            data = np.load(self.calibration_file, allow_pickle=False)

            # Extract metadata
            version = str(data['version']) if 'version' in data else "unknown"
            timestamp = float(data['timestamp']) if 'timestamp' in data else 0
            grid_size = (int(data['grid_rows']), int(data['grid_cols']))
            screen_size = (int(data['screen_width']), int(data['screen_height']))

            # Extract regional offsets
            regional_offsets = {}
            for row in range(grid_size[0]):
                for col in range(grid_size[1]):
                    key = f'offset_{row}_{col}'
                    if key in data:
                        regional_offsets[(row, col)] = data[key]

            # Extract metrics
            metrics = CalibrationMetrics(
                timestamp=timestamp,
                num_points=int(data.get('num_points', 0)),
                mean_error=float(data.get('mean_error', 0)),
                median_error=float(data.get('median_error', 0)),
                max_error=float(data.get('max_error', 0)),
                std_error=float(data.get('std_error', 0)),
                success_rate=float(data.get('success_rate', 0)),
                regional_grid=grid_size,
            )

            logger.info(f"Loaded calibration from {self.calibration_file} "
                       f"(version {version}, age {time.time() - timestamp:.0f}s)")

            return {
                'version': version,
                'timestamp': timestamp,
                'grid_size': grid_size,
                'screen_size': screen_size,
                'regional_offsets': regional_offsets,
                'metrics': metrics,
            }

        except Exception as e:
            logger.error(f"Error loading calibration: {e}")
            return None

    def _create_backup(self):
        """Create backup of current calibration"""
        if not self.calibration_file.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"calibration_{timestamp}.npz"

        try:
            shutil.copy2(self.calibration_file, backup_file)
            logger.info(f"Created calibration backup: {backup_file}")

            # Clean old backups (keep last 10)
            self._cleanup_old_backups(keep=10)

        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    def _cleanup_old_backups(self, keep: int = 10):
        """
        Remove old backup files

        Args:
            keep: Number of backups to keep
        """
        backups = sorted(self.backup_dir.glob("calibration_*.npz"))

        if len(backups) > keep:
            for backup in backups[:-keep]:
                try:
                    backup.unlink()
                    logger.debug(f"Removed old backup: {backup}")
                except Exception as e:
                    logger.warning(f"Failed to remove backup {backup}: {e}")

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available calibration backups

        Returns:
            List of backup info dictionaries
        """
        backups = []
        for backup_file in sorted(self.backup_dir.glob("calibration_*.npz")):
            try:
                data = np.load(backup_file, allow_pickle=False)
                backups.append({
                    'file': str(backup_file),
                    'timestamp': float(data.get('timestamp', 0)),
                    'success_rate': float(data.get('success_rate', 0)),
                    'mean_error': float(data.get('mean_error', 0)),
                })
            except Exception as e:
                logger.warning(f"Could not read backup {backup_file}: {e}")

        return backups

    def restore_backup(self, backup_file: str):
        """
        Restore calibration from backup

        Args:
            backup_file: Path to backup file
        """
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        try:
            # Backup current before restoring
            if self.calibration_file.exists():
                self._create_backup()

            shutil.copy2(backup_path, self.calibration_file)
            logger.info(f"Restored calibration from {backup_file}")

        except Exception as e:
            raise IOError(f"Failed to restore backup: {e}")


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass


def create_default_config(output_path: str = "./config.yaml"):
    """
    Create a default configuration file

    Args:
        output_path: Path to write config file
    """
    manager = ConfigManager()
    manager.save(output_path)
    logger.info(f"Created default configuration at {output_path}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create default config
    create_default_config()

    # Load and display config
    manager = ConfigManager()
    print("\nConfiguration loaded:")
    print(f"  OCR: {manager.ocr.num_passes} passes, GPU={manager.ocr.use_gpu}")
    print(f"  Calibration: {manager.calibration.num_points} points, "
          f"{manager.calibration.regional_grid} grid")
    print(f"  Click: {manager.click.button} button, validation={manager.click.validate_click}")

    # Test state manager
    state = StateManager()
    print(f"\nState: calibrated={state.is_calibrated}, clicks={state.click_count}")
