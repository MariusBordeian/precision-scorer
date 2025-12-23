"""
Target and hole detection module.
Uses multiple detection strategies for robustness.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .config import TargetConfig, AppSettings


@dataclass
class DetectedCircle:
    """A detected circular feature in the image."""
    center_x: float
    center_y: float
    radius: float
    intensity: float = 0
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.center_x, self.center_y)


@dataclass
class TargetCalibration:
    """Calibration data after detecting the target in an image."""
    center_x: float
    center_y: float
    radius_px: float
    pixels_per_mm: float
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.center_x, self.center_y)
    
    def mm_to_px(self, mm: float) -> float:
        return mm * self.pixels_per_mm
    
    def px_to_mm(self, px: float) -> float:
        return px / self.pixels_per_mm


def detect_target_circles(gray_image: np.ndarray) -> Optional[Tuple[float, float, float]]:
    """
    Detect the target's circular rings using Hough Circles.
    Returns (center_x, center_y, radius) of the detected target.
    """
    height, width = gray_image.shape
    min_dim = min(height, width)
    
    # Apply edge detection to find the rings
    blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
    
    # Try to find circles of various sizes
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_dim // 4,
        param1=80,
        param2=40,
        minRadius=min_dim // 10,
        maxRadius=min_dim // 2
    )
    
    if circles is not None and len(circles[0]) > 0:
        # Find the circle closest to image center with reasonable size
        img_center = (width / 2, height / 2)
        best_circle = None
        best_score = float('inf')
        
        for circle in circles[0]:
            x, y, r = circle
            # Distance from image center
            dist = np.sqrt((x - img_center[0])**2 + (y - img_center[1])**2)
            # Prefer circles near center and of reasonable size
            score = dist + abs(r - min_dim * 0.3) * 0.5
            if score < best_score:
                best_score = score
                best_circle = (float(x), float(y), float(r))
        
        return best_circle
    
    return None


def detect_target(
    gray_image: np.ndarray,
    target_config: TargetConfig
) -> Optional[TargetCalibration]:
    """
    Detect the target in the image and establish calibration.
    Tries to find actual circular target, falls back to center estimation.
    """
    height, width = gray_image.shape
    min_dim = min(height, width)
    
    # Try to detect actual target circles
    detected = detect_target_circles(gray_image)
    
    if detected is not None:
        center_x, center_y, radius_px = detected
        # Assume detected ring is roughly the black area boundary
        pixels_per_mm = (radius_px * 2) / target_config.black_area_diameter_mm
    else:
        # Fallback: use image center, estimate smaller target size
        center_x = width / 2
        center_y = height / 2
        # Assume target takes about 60% of smaller dimension
        radius_px = min_dim * 0.30
        pixels_per_mm = (radius_px * 2) / target_config.black_area_diameter_mm
    
    return TargetCalibration(
        center_x=float(center_x),
        center_y=float(center_y),
        radius_px=float(radius_px),
        pixels_per_mm=float(pixels_per_mm)
    )


def find_holes_adaptive(
    gray_image: np.ndarray,
    calibration: TargetCalibration,
    target_config: TargetConfig
) -> List[DetectedCircle]:
    """
    Find holes using blob detection within the calibrated area.
    Uses SimpleBlobDetector for more reliable hole detection.
    """
    holes = []
    
    # Calculate expected hole size
    bullet_radius_px = calibration.mm_to_px(target_config.bullet_diameter_mm / 2)
    min_radius = max(3, int(bullet_radius_px * 0.5))
    max_radius = max(min_radius + 5, int(bullet_radius_px * 2.5))
    
    # Duplicate distance - holes can't be closer than bullet diameter
    min_hole_distance = max(8, int(bullet_radius_px * 1.5))
    
    # Create a mask for the calibrated area
    area_mask = np.zeros(gray_image.shape, dtype=np.uint8)
    cv2.circle(area_mask, (int(calibration.center_x), int(calibration.center_y)), 
               int(calibration.radius_px), 255, -1)
    
    # Apply mask
    masked_gray = cv2.bitwise_and(gray_image, area_mask)
    
    # Setup SimpleBlobDetector parameters
    params = cv2.SimpleBlobDetector_Params()
    
    # Filter by area
    params.filterByArea = True
    params.minArea = 3.14159 * (min_radius ** 2)
    params.maxArea = 3.14159 * (max_radius ** 2)
    
    # Filter by circularity
    params.filterByCircularity = True
    params.minCircularity = 0.55
    
    # Filter by convexity
    params.filterByConvexity = True
    params.minConvexity = 0.7
    
    # Filter by inertia (roundness)
    params.filterByInertia = True
    params.minInertiaRatio = 0.4
    
    # Don't filter by color - we'll try both
    params.filterByColor = False
    
    detector = cv2.SimpleBlobDetector_create(params)
    
    # Try detection on both normal and inverted image
    for invert in [False, True]:
        if invert:
            img_to_detect = cv2.bitwise_not(masked_gray)
        else:
            img_to_detect = masked_gray
        
        keypoints = detector.detect(img_to_detect)
        
        for kp in keypoints:
            x, y = kp.pt
            radius = kp.size / 2
            
            # Check if within calibrated area
            dist_from_center = np.sqrt(
                (x - calibration.center_x) ** 2 +
                (y - calibration.center_y) ** 2
            )
            
            if dist_from_center > calibration.radius_px:
                continue
            
            # Check for duplicates
            duplicate = False
            for h in holes:
                if np.sqrt((x - h.center_x)**2 + (y - h.center_y)**2) < min_hole_distance:
                    duplicate = True
                    break
            
            if not duplicate:
                holes.append(DetectedCircle(
                    center_x=float(x),
                    center_y=float(y),
                    radius=float(max(radius, min_radius)),
                    intensity=0.0
                ))
    
    # Sort by distance from center (closest first)
    holes.sort(key=lambda h: np.sqrt(
        (h.center_x - calibration.center_x) ** 2 +
        (h.center_y - calibration.center_y) ** 2
    ))
    
    return holes


def detect_all(
    gray_image: np.ndarray,
    target_config: TargetConfig,
    color_image: Optional[np.ndarray] = None
) -> Tuple[Optional[TargetCalibration], List[DetectedCircle]]:
    """
    Full detection pipeline: find target, then find holes.
    """
    calibration = detect_target(gray_image, target_config)
    
    if calibration is None:
        return None, []
    
    holes = find_holes_adaptive(gray_image, calibration, target_config)
    
    return calibration, holes
