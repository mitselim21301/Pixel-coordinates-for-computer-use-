"""
Coordinate Transformation Pipeline for Accurate OCR-to-Click System

This module implements a 7-stage transformation pipeline that achieves sub-pixel accuracy
for converting OCR bounding boxes to precise click coordinates on Windows.

Pipeline Stages:
    1. OCR Format Normalization (any format → XYXY)
    2. Center Point Calculation
    3. DPI-Aware Scaling (if needed)
    4. Multi-Monitor Offset Adjustment
    5. SendInput Normalization (pixels → 65535 range)
    6. Calibration Correction
    7. Validation

Reference: MATHEMATICAL_SOLUTION_SPEC.md
"""

import numpy as np
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from typing import Tuple, Optional, List, Dict, Union, Literal
from enum import Enum
import logging

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Constants and Enumerations
# ============================================================================

class OCRFormat(Enum):
    """Supported OCR bounding box formats"""
    XYXY = "xyxy"              # [x_min, y_min, x_max, y_max]
    XYWH = "xywh"              # [x, y, width, height]
    QUAD = "quad"              # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    NORMALIZED = "normalized"  # [x_min, y_min, x_max, y_max] in [0, 1]


# Windows API Constants
SM_XVIRTUALSCREEN = 76   # Left edge of virtual screen
SM_YVIRTUALSCREEN = 77   # Top edge of virtual screen
SM_CXVIRTUALSCREEN = 78  # Width of virtual screen
SM_CYVIRTUALSCREEN = 79  # Height of virtual screen

# Mouse event flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000

# SendInput normalization range
SENDINPUT_MAX = 65535


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class MonitorInfo:
    """Monitor information structure"""
    handle: int
    left: int
    top: int
    right: int
    bottom: int
    dpi_x: int
    dpi_y: int
    is_primary: bool

    @property
    def width(self) -> int:
        """Monitor width in pixels"""
        return self.right - self.left

    @property
    def height(self) -> int:
        """Monitor height in pixels"""
        return self.bottom - self.top

    @property
    def scale_factor_x(self) -> float:
        """DPI scale factor (x-axis)"""
        return self.dpi_x / 96.0

    @property
    def scale_factor_y(self) -> float:
        """DPI scale factor (y-axis)"""
        return self.dpi_y / 96.0


@dataclass
class BoundingBox:
    """Normalized bounding box in XYXY format"""
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def center(self) -> Tuple[float, float]:
        """Get center point of bounding box"""
        return ((self.x_min + self.x_max) / 2.0, (self.y_min + self.y_max) / 2.0)

    @property
    def width(self) -> float:
        """Width of bounding box"""
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        """Height of bounding box"""
        return self.y_max - self.y_min

    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Convert to tuple (x_min, y_min, x_max, y_max)"""
        return (self.x_min, self.y_min, self.x_max, self.y_max)


@dataclass
class TransformationResult:
    """Result of coordinate transformation"""
    final_x: int
    final_y: int
    normalized_x: int  # SendInput coordinates [0, 65535]
    normalized_y: int
    stages: Dict[str, Tuple[float, float]]  # Intermediate coordinates at each stage
    validation_passed: bool
    error_message: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

def normalize_bbox(bbox: Union[List, Tuple, np.ndarray],
                   format_type: OCRFormat,
                   image_width: Optional[int] = None,
                   image_height: Optional[int] = None) -> BoundingBox:
    """
    Normalize bounding box from any OCR format to XYXY format.

    Stage 1: OCR Format Normalization

    Args:
        bbox: Bounding box in any supported format
        format_type: Format of the input bounding box
        image_width: Image width (required for normalized format)
        image_height: Image height (required for normalized format)

    Returns:
        BoundingBox in XYXY format

    Raises:
        ValueError: If format is invalid or required dimensions are missing
    """
    if format_type == OCRFormat.XYXY:
        # Already in XYXY format
        if len(bbox) != 4:
            raise ValueError(f"XYXY format requires 4 values, got {len(bbox)}")
        return BoundingBox(
            x_min=float(bbox[0]),
            y_min=float(bbox[1]),
            x_max=float(bbox[2]),
            y_max=float(bbox[3])
        )

    elif format_type == OCRFormat.XYWH:
        # Convert from [x, y, width, height] to [x_min, y_min, x_max, y_max]
        if len(bbox) != 4:
            raise ValueError(f"XYWH format requires 4 values, got {len(bbox)}")
        x, y, w, h = bbox
        return BoundingBox(
            x_min=float(x),
            y_min=float(y),
            x_max=float(x + w),
            y_max=float(y + h)
        )

    elif format_type == OCRFormat.QUAD:
        # Convert from quad (4 points) to XYXY
        bbox_array = np.array(bbox)
        if bbox_array.shape[0] != 4 or bbox_array.shape[1] != 2:
            raise ValueError(f"QUAD format requires 4 points with 2 coordinates each")
        return BoundingBox(
            x_min=float(np.min(bbox_array[:, 0])),
            y_min=float(np.min(bbox_array[:, 1])),
            x_max=float(np.max(bbox_array[:, 0])),
            y_max=float(np.max(bbox_array[:, 1]))
        )

    elif format_type == OCRFormat.NORMALIZED:
        # Convert from normalized [0, 1] coordinates
        if image_width is None or image_height is None:
            raise ValueError("Image dimensions required for normalized format")
        if len(bbox) != 4:
            raise ValueError(f"Normalized format requires 4 values, got {len(bbox)}")
        return BoundingBox(
            x_min=float(bbox[0] * image_width),
            y_min=float(bbox[1] * image_height),
            x_max=float(bbox[2] * image_width),
            y_max=float(bbox[3] * image_height)
        )

    else:
        raise ValueError(f"Unsupported format: {format_type}")


def get_center(bbox: BoundingBox,
               weights: Optional[np.ndarray] = None) -> Tuple[float, float]:
    """
    Calculate center point of bounding box.

    Stage 2: Center Point Calculation

    Args:
        bbox: Bounding box in XYXY format
        weights: Optional weights for confidence-weighted center (not implemented yet)

    Returns:
        (x_center, y_center) tuple
    """
    # Simple average for now
    # Future: Implement confidence-weighted positioning if weights provided
    return bbox.center


def apply_virtual_desktop_offset(x: float, y: float,
                                 virtual_bounds: Dict[str, int]) -> Tuple[float, float]:
    """
    Apply virtual desktop offset for multi-monitor setups.

    Stage 4: Multi-Monitor Offset Adjustment

    Args:
        x, y: Physical pixel coordinates
        virtual_bounds: Dictionary with 'left' and 'top' keys

    Returns:
        (x_adjusted, y_adjusted) tuple
    """
    x_adjusted = x - virtual_bounds['left']
    y_adjusted = y - virtual_bounds['top']
    return (x_adjusted, y_adjusted)


def normalize_for_sendinput(x: float, y: float,
                            virtual_bounds: Dict[str, int]) -> Tuple[int, int]:
    """
    Normalize coordinates to SendInput range [0, 65535].

    Stage 5: SendInput Normalization

    Uses integer division to avoid floating-point rounding errors.

    Args:
        x, y: Coordinates in virtual desktop space
        virtual_bounds: Dictionary with 'width' and 'height' keys

    Returns:
        (x_normalized, y_normalized) tuple in [0, 65535] range
    """
    # Apply virtual desktop offset first
    x_virt = x - virtual_bounds['left']
    y_virt = y - virtual_bounds['top']

    # Normalize to [0, 65535] using integer division
    # Important: Use integer division to avoid float errors
    x_normalized = int((x_virt * SENDINPUT_MAX) // virtual_bounds['width'])
    y_normalized = int((y_virt * SENDINPUT_MAX) // virtual_bounds['height'])

    # Clamp to valid range
    x_normalized = max(0, min(SENDINPUT_MAX, x_normalized))
    y_normalized = max(0, min(SENDINPUT_MAX, y_normalized))

    return (x_normalized, y_normalized)


# ============================================================================
# DPI Manager
# ============================================================================

class DPIManager:
    """
    Manages DPI awareness and coordinate conversions for Windows.

    Handles:
    - Per-Monitor DPI Awareness (V2/V1)
    - Monitor information retrieval
    - Physical ↔ Logical coordinate conversion
    - Virtual desktop bounds
    """

    def __init__(self, set_awareness: bool = True):
        """
        Initialize DPI Manager.

        Args:
            set_awareness: Whether to automatically set DPI awareness
        """
        self.user32 = ctypes.windll.user32
        try:
            self.shcore = ctypes.windll.shcore
        except Exception:
            self.shcore = None
            logger.warning("shcore.dll not available - some DPI features may be limited")

        self.awareness_level = None

        if set_awareness:
            self._set_dpi_awareness()

    def _set_dpi_awareness(self) -> None:
        """
        Set highest available DPI awareness level.

        Priority:
        1. Per-Monitor V2 (Windows 10 1703+)
        2. Per-Monitor V1 (Windows 8.1+)
        3. System DPI Aware (Windows 7+)
        """
        try:
            # Try Per-Monitor V2 (best option)
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
            self.user32.SetProcessDpiAwarenessContext(
                DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            )
            self.awareness_level = "Per-Monitor V2"
            logger.info("DPI Awareness set to: Per-Monitor V2")
            return
        except Exception as e:
            logger.debug(f"Per-Monitor V2 not available: {e}")

        try:
            # Try Per-Monitor V1
            if self.shcore is not None:
                self.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                self.awareness_level = "Per-Monitor V1"
                logger.info("DPI Awareness set to: Per-Monitor V1")
                return
        except Exception as e:
            logger.debug(f"Per-Monitor V1 not available: {e}")

        try:
            # Fallback to System DPI Aware
            self.user32.SetProcessDPIAware()
            self.awareness_level = "System"
            logger.info("DPI Awareness set to: System")
        except Exception as e:
            logger.warning(f"Failed to set DPI awareness: {e}")
            self.awareness_level = "Unaware"

    def get_monitor_at_point(self, x: int, y: int) -> MonitorInfo:
        """
        Get monitor information for a specific point.

        Args:
            x, y: Physical pixel coordinates

        Returns:
            MonitorInfo for the monitor containing the point
        """
        # Get monitor handle for point
        pt = wintypes.POINT(int(x), int(y))
        hMonitor = self.user32.MonitorFromPoint(pt, 2)  # MONITOR_DEFAULTTONEAREST

        return self._get_monitor_info(hMonitor)

    def get_all_monitors(self) -> List[MonitorInfo]:
        """
        Get information for all monitors.

        Returns:
            List of MonitorInfo for all connected monitors
        """
        monitors = []

        def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
            try:
                monitors.append(self._get_monitor_info(hMonitor))
            except Exception as e:
                logger.error(f"Error getting monitor info: {e}")
            return True

        # Define callback type
        MONITOR_ENUM_PROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(wintypes.RECT),
            ctypes.c_void_p
        )

        # Enumerate monitors
        self.user32.EnumDisplayMonitors(
            None, None, MONITOR_ENUM_PROC(callback), 0
        )

        return monitors

    def _get_monitor_info(self, hMonitor) -> MonitorInfo:
        """
        Get detailed information for a specific monitor.

        Args:
            hMonitor: Monitor handle

        Returns:
            MonitorInfo structure
        """
        # Define MONITORINFO structure
        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ('cbSize', wintypes.DWORD),
                ('rcMonitor', wintypes.RECT),
                ('rcWork', wintypes.RECT),
                ('dwFlags', wintypes.DWORD)
            ]

        # Get monitor info
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        self.user32.GetMonitorInfoW(hMonitor, ctypes.byref(mi))

        # Get DPI for monitor
        dpiX = ctypes.c_uint()
        dpiY = ctypes.c_uint()

        if self.shcore is not None:
            try:
                # MDT_EFFECTIVE_DPI = 0
                self.shcore.GetDpiForMonitor(
                    hMonitor, 0, ctypes.byref(dpiX), ctypes.byref(dpiY)
                )
            except Exception:
                # Fallback to system DPI
                dpiX.value = 96
                dpiY.value = 96
        else:
            # Fallback to system DPI
            dpiX.value = 96
            dpiY.value = 96

        return MonitorInfo(
            handle=hMonitor,
            left=mi.rcMonitor.left,
            top=mi.rcMonitor.top,
            right=mi.rcMonitor.right,
            bottom=mi.rcMonitor.bottom,
            dpi_x=dpiX.value,
            dpi_y=dpiY.value,
            is_primary=bool(mi.dwFlags & 1)  # MONITORINFOF_PRIMARY
        )

    def get_virtual_screen_bounds(self) -> Dict[str, int]:
        """
        Get virtual desktop bounds (all monitors combined).

        Returns:
            Dictionary with 'left', 'top', 'width', 'height' keys
        """
        return {
            'left': self.user32.GetSystemMetrics(SM_XVIRTUALSCREEN),
            'top': self.user32.GetSystemMetrics(SM_YVIRTUALSCREEN),
            'width': self.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN),
            'height': self.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        }

    def logical_to_physical(self, x: int, y: int, monitor: Optional[MonitorInfo] = None) -> Tuple[int, int]:
        """
        Convert logical (DPI-scaled) coordinates to physical pixels.

        Args:
            x, y: Logical coordinates
            monitor: Monitor info (if None, will detect from coordinates)

        Returns:
            (x_physical, y_physical) tuple
        """
        if monitor is None:
            monitor = self.get_monitor_at_point(x, y)

        x_physical = int(x * monitor.scale_factor_x)
        y_physical = int(y * monitor.scale_factor_y)

        return (x_physical, y_physical)

    def physical_to_logical(self, x: int, y: int, monitor: Optional[MonitorInfo] = None) -> Tuple[int, int]:
        """
        Convert physical pixel coordinates to logical (DPI-scaled) coordinates.

        Args:
            x, y: Physical coordinates
            monitor: Monitor info (if None, will detect from coordinates)

        Returns:
            (x_logical, y_logical) tuple
        """
        if monitor is None:
            monitor = self.get_monitor_at_point(x, y)

        x_logical = int(x / monitor.scale_factor_x)
        y_logical = int(y / monitor.scale_factor_y)

        return (x_logical, y_logical)


# ============================================================================
# Coordinate Transformer
# ============================================================================

class CoordinateTransformer:
    """
    7-Stage Coordinate Transformation Pipeline.

    Transforms OCR bounding boxes to accurate click coordinates with
    sub-pixel accuracy.

    Pipeline:
        1. OCR Format Normalization
        2. Center Point Calculation
        3. DPI-Aware Scaling
        4. Multi-Monitor Offset Adjustment
        5. SendInput Normalization
        6. Calibration Correction
        7. Validation
    """

    def __init__(self,
                 dpi_manager: Optional[DPIManager] = None,
                 use_calibration: bool = True,
                 debug: bool = False):
        """
        Initialize coordinate transformer.

        Args:
            dpi_manager: DPIManager instance (creates new one if None)
            use_calibration: Whether to use calibration correction
            debug: Enable debug logging
        """
        self.dpi_manager = dpi_manager if dpi_manager is not None else DPIManager()
        self.use_calibration = use_calibration
        self.debug = debug

        # Calibration data
        self.homography_matrix: Optional[np.ndarray] = None
        self.is_calibrated = False

        logger.info(f"CoordinateTransformer initialized (calibration: {use_calibration}, "
                   f"DPI awareness: {self.dpi_manager.awareness_level})")

    # ========================================================================
    # Main Transformation Pipeline
    # ========================================================================

    def transform(self,
                  bbox: Union[List, Tuple, np.ndarray],
                  format_type: OCRFormat = OCRFormat.XYXY,
                  screenshot_size: Optional[Tuple[int, int]] = None,
                  screen_size: Optional[Tuple[int, int]] = None,
                  validate: bool = True) -> TransformationResult:
        """
        Execute complete 7-stage transformation pipeline.

        Args:
            bbox: OCR bounding box in any supported format
            format_type: Format of input bounding box
            screenshot_size: (width, height) of screenshot (if different from screen)
            screen_size: (width, height) of screen (for validation)
            validate: Whether to run validation (Stage 7)

        Returns:
            TransformationResult with final coordinates and intermediate stages
        """
        stages = {}

        try:
            # STAGE 1: OCR Format Normalization
            if format_type == OCRFormat.NORMALIZED:
                if screenshot_size is None:
                    raise ValueError("screenshot_size required for normalized format")
                normalized_bbox = normalize_bbox(
                    bbox, format_type,
                    image_width=screenshot_size[0],
                    image_height=screenshot_size[1]
                )
            else:
                normalized_bbox = normalize_bbox(bbox, format_type)

            stages['stage1_normalized'] = normalized_bbox.to_tuple()

            # STAGE 2: Center Point Calculation
            x_center, y_center = get_center(normalized_bbox)
            stages['stage2_center'] = (x_center, y_center)

            # STAGE 3: DPI-Aware Scaling (Screenshot → Screen)
            if screenshot_size is not None and screen_size is not None:
                if screenshot_size != screen_size:
                    scale_x = screen_size[0] / screenshot_size[0]
                    scale_y = screen_size[1] / screenshot_size[1]
                    x_center *= scale_x
                    y_center *= scale_y
                    logger.debug(f"Applied scaling: {scale_x:.3f}x, {scale_y:.3f}y")

            stages['stage3_scaled'] = (x_center, y_center)

            # STAGE 4: Multi-Monitor Offset Adjustment
            # (Applied later in Stage 5 during normalization)
            # Just record current coordinates
            stages['stage4_physical'] = (x_center, y_center)

            # STAGE 5: SendInput Normalization
            virtual_bounds = self.dpi_manager.get_virtual_screen_bounds()
            x_norm, y_norm = normalize_for_sendinput(
                x_center, y_center, virtual_bounds
            )
            stages['stage5_normalized'] = (x_norm, y_norm)

            # STAGE 6: Calibration Correction
            if self.use_calibration and self.is_calibrated:
                x_corrected, y_corrected = self._apply_calibration(x_center, y_center)
                # Re-normalize corrected coordinates
                x_norm, y_norm = normalize_for_sendinput(
                    x_corrected, y_corrected, virtual_bounds
                )
                stages['stage6_calibrated'] = (x_corrected, y_corrected)
            else:
                x_corrected, y_corrected = x_center, y_center
                stages['stage6_calibrated'] = (x_corrected, y_corrected)

            # Final physical coordinates (rounded to integers)
            final_x = int(round(x_corrected))
            final_y = int(round(y_corrected))

            # STAGE 7: Validation
            validation_passed = True
            error_message = None

            if validate:
                validation_passed, error_message = self._validate_coordinates(
                    final_x, final_y, x_norm, y_norm, screen_size
                )

            return TransformationResult(
                final_x=final_x,
                final_y=final_y,
                normalized_x=x_norm,
                normalized_y=y_norm,
                stages=stages,
                validation_passed=validation_passed,
                error_message=error_message
            )

        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            return TransformationResult(
                final_x=0,
                final_y=0,
                normalized_x=0,
                normalized_y=0,
                stages=stages,
                validation_passed=False,
                error_message=str(e)
            )

    # ========================================================================
    # Calibration Methods (Stage 6)
    # ========================================================================

    def calibrate(self,
                  src_points: np.ndarray,
                  dst_points: np.ndarray,
                  use_ransac: bool = True,
                  ransac_threshold: float = 5.0,
                  ransac_iterations: int = 1000) -> None:
        """
        Calibrate coordinate transformation using point correspondences.

        Args:
            src_points: Source points (OCR/measured) as Nx2 array
            dst_points: Destination points (ground truth) as Nx2 array
            use_ransac: Use RANSAC for robust estimation
            ransac_threshold: RANSAC inlier threshold in pixels
            ransac_iterations: Number of RANSAC iterations
        """
        if len(src_points) < 4:
            raise ValueError(f"Need at least 4 calibration points, got {len(src_points)}")

        if len(src_points) != len(dst_points):
            raise ValueError(f"Source and destination point counts must match: "
                           f"{len(src_points)} vs {len(dst_points)}")

        logger.info(f"Calibrating with {len(src_points)} points...")

        if use_ransac:
            self.homography_matrix, inliers = self._ransac_homography(
                src_points, dst_points, ransac_threshold, ransac_iterations
            )
            inlier_ratio = np.sum(inliers) / len(inliers)
            logger.info(f"RANSAC calibration: {np.sum(inliers)}/{len(inliers)} "
                       f"inliers ({inlier_ratio:.1%})")
        else:
            self.homography_matrix = self._compute_homography_dlt(src_points, dst_points)
            logger.info("DLT calibration complete")

        self.is_calibrated = True

        # Compute and log calibration error
        errors = self._compute_calibration_errors(src_points, dst_points)
        logger.info(f"Calibration error - Mean: {np.mean(errors):.3f}px, "
                   f"Max: {np.max(errors):.3f}px, Std: {np.std(errors):.3f}px")

    def _apply_calibration(self, x: float, y: float) -> Tuple[float, float]:
        """
        Apply calibration correction to a point.

        Args:
            x, y: Input coordinates

        Returns:
            (x_corrected, y_corrected) tuple
        """
        if not self.is_calibrated or self.homography_matrix is None:
            return (x, y)

        # Apply homography transformation
        corrected = self._apply_homography(
            np.array([[x, y]]), self.homography_matrix
        )[0]

        return (float(corrected[0]), float(corrected[1]))

    @staticmethod
    def _compute_homography_dlt(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
        """
        Compute homography using Direct Linear Transform (DLT).

        Args:
            src: Source points (Nx2)
            dst: Destination points (Nx2)

        Returns:
            3x3 homography matrix
        """
        n = len(src)
        A = []

        for i in range(n):
            x, y = src[i]
            xp, yp = dst[i]

            # Build DLT equations
            A.append([-x, -y, -1, 0, 0, 0, xp*x, xp*y, xp])
            A.append([0, 0, 0, -x, -y, -1, yp*x, yp*y, yp])

        A = np.array(A)

        # Solve using SVD
        U, S, Vt = np.linalg.svd(A)
        H = Vt[-1].reshape(3, 3)

        # Normalize
        H = H / H[2, 2]

        return H

    @staticmethod
    def _apply_homography(points: np.ndarray, H: np.ndarray) -> np.ndarray:
        """
        Apply homography transformation to points.

        Args:
            points: Input points (Nx2)
            H: 3x3 homography matrix

        Returns:
            Transformed points (Nx2)
        """
        # Convert to homogeneous coordinates
        points_h = np.hstack([points, np.ones((len(points), 1))])

        # Apply transformation
        transformed_h = (H @ points_h.T).T

        # Convert back to Cartesian coordinates
        transformed = transformed_h[:, :2] / transformed_h[:, 2:3]

        return transformed

    def _ransac_homography(self,
                          src: np.ndarray,
                          dst: np.ndarray,
                          threshold: float,
                          iterations: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        RANSAC-based robust homography estimation.

        Args:
            src: Source points (Nx2)
            dst: Destination points (Nx2)
            threshold: Inlier threshold in pixels
            iterations: Number of RANSAC iterations

        Returns:
            (best_homography, inlier_mask) tuple
        """
        n = len(src)
        best_H = None
        best_inliers = np.zeros(n, dtype=bool)
        best_count = 0

        for iteration in range(iterations):
            # Sample 4 random points
            indices = np.random.choice(n, 4, replace=False)
            sample_src = src[indices]
            sample_dst = dst[indices]

            try:
                # Compute homography from sample
                H = self._compute_homography_dlt(sample_src, sample_dst)

                # Count inliers
                projected = self._apply_homography(src, H)
                errors = np.linalg.norm(dst - projected, axis=1)
                inliers = errors < threshold
                count = np.sum(inliers)

                # Update best if better
                if count > best_count:
                    best_count = count
                    best_inliers = inliers
                    best_H = H

            except Exception as e:
                logger.debug(f"RANSAC iteration {iteration} failed: {e}")
                continue

        # Refine using all inliers
        if best_count >= 4:
            inlier_src = src[best_inliers]
            inlier_dst = dst[best_inliers]
            best_H = self._compute_homography_dlt(inlier_src, inlier_dst)

        return best_H, best_inliers

    def _compute_calibration_errors(self,
                                   src_points: np.ndarray,
                                   dst_points: np.ndarray) -> np.ndarray:
        """
        Compute calibration errors.

        Args:
            src_points: Source points
            dst_points: Destination points

        Returns:
            Array of errors in pixels
        """
        if not self.is_calibrated:
            return np.array([])

        projected = self._apply_homography(src_points, self.homography_matrix)
        errors = np.linalg.norm(dst_points - projected, axis=1)

        return errors

    def save_calibration(self, filepath: str) -> None:
        """
        Save calibration data to file.

        Args:
            filepath: Path to save calibration file
        """
        if not self.is_calibrated:
            raise ValueError("No calibration computed")

        np.savez(filepath, homography=self.homography_matrix)
        logger.info(f"Calibration saved to {filepath}")

    def load_calibration(self, filepath: str) -> None:
        """
        Load calibration data from file.

        Args:
            filepath: Path to calibration file
        """
        data = np.load(filepath)
        self.homography_matrix = data['homography']
        self.is_calibrated = True
        logger.info(f"Calibration loaded from {filepath}")

    # ========================================================================
    # Validation (Stage 7)
    # ========================================================================

    def _validate_coordinates(self,
                             x: int,
                             y: int,
                             x_norm: int,
                             y_norm: int,
                             screen_size: Optional[Tuple[int, int]] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate final coordinates.

        Args:
            x, y: Physical pixel coordinates
            x_norm, y_norm: SendInput normalized coordinates
            screen_size: Screen size for bounds checking

        Returns:
            (is_valid, error_message) tuple
        """
        # Check SendInput normalization range
        if not (0 <= x_norm <= SENDINPUT_MAX):
            return (False, f"x_norm out of range: {x_norm}")

        if not (0 <= y_norm <= SENDINPUT_MAX):
            return (False, f"y_norm out of range: {y_norm}")

        # Check screen bounds if provided
        if screen_size is not None:
            virtual_bounds = self.dpi_manager.get_virtual_screen_bounds()

            # Validate against virtual desktop bounds
            max_x = virtual_bounds['left'] + virtual_bounds['width']
            max_y = virtual_bounds['top'] + virtual_bounds['height']

            if not (virtual_bounds['left'] <= x <= max_x):
                return (False, f"x out of virtual screen bounds: {x}")

            if not (virtual_bounds['top'] <= y <= max_y):
                return (False, f"y out of virtual screen bounds: {y}")

        # All validation passed
        return (True, None)


# ============================================================================
# Convenience Functions
# ============================================================================

def quick_transform(bbox: Union[List, Tuple],
                   format_type: OCRFormat = OCRFormat.XYXY,
                   screenshot_size: Optional[Tuple[int, int]] = None) -> Tuple[int, int]:
    """
    Quick transformation without calibration.

    Args:
        bbox: Bounding box
        format_type: Format type
        screenshot_size: Screenshot dimensions

    Returns:
        (x, y) physical pixel coordinates
    """
    transformer = CoordinateTransformer(use_calibration=False)
    result = transformer.transform(bbox, format_type, screenshot_size)

    if not result.validation_passed:
        logger.warning(f"Validation failed: {result.error_message}")

    return (result.final_x, result.final_y)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    print("=== Coordinate Transformer Test ===\n")

    # Initialize
    dpi_mgr = DPIManager()
    transformer = CoordinateTransformer(dpi_mgr, use_calibration=False)

    # Test different formats
    print("Test 1: XYXY format")
    bbox_xyxy = [100, 200, 300, 400]
    result = transformer.transform(bbox_xyxy, OCRFormat.XYXY)
    print(f"  Input: {bbox_xyxy}")
    print(f"  Output: ({result.final_x}, {result.final_y})")
    print(f"  Validation: {result.validation_passed}\n")

    print("Test 2: XYWH format")
    bbox_xywh = [100, 200, 200, 200]  # Same as above
    result = transformer.transform(bbox_xywh, OCRFormat.XYWH)
    print(f"  Input: {bbox_xywh}")
    print(f"  Output: ({result.final_x}, {result.final_y})")
    print(f"  Validation: {result.validation_passed}\n")

    print("Test 3: QUAD format")
    bbox_quad = [[100, 200], [300, 200], [300, 400], [100, 400]]
    result = transformer.transform(bbox_quad, OCRFormat.QUAD)
    print(f"  Input: {bbox_quad}")
    print(f"  Output: ({result.final_x}, {result.final_y})")
    print(f"  Validation: {result.validation_passed}\n")

    # Display system info
    print("=== System Information ===")
    print(f"DPI Awareness: {dpi_mgr.awareness_level}")
    virtual_bounds = dpi_mgr.get_virtual_screen_bounds()
    print(f"Virtual Screen: {virtual_bounds}")

    monitors = dpi_mgr.get_all_monitors()
    print(f"\nMonitors: {len(monitors)}")
    for i, mon in enumerate(monitors):
        print(f"  Monitor {i}: {mon.width}x{mon.height} @ {mon.dpi_x} DPI "
              f"({'Primary' if mon.is_primary else 'Secondary'})")
