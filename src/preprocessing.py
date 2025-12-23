"""
Image preprocessing module.
Handles image loading, enhancement, and perspective correction.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple


def load_image(path: str | Path) -> np.ndarray:
    """Load an image from file path."""
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Could not load image: {path}")
    return img


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert image to grayscale."""
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def apply_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Apply Gaussian blur to reduce noise."""
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(image)


def detect_screen_corners(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Attempt to detect a rectangular screen/monitor in the image.
    Returns 4 corner points if found, None otherwise.
    """
    gray = to_grayscale(image)
    blurred = apply_blur(gray, 5)
    edges = cv2.Canny(blurred, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Look for large rectangular contours
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        if len(approx) == 4:
            # Check if it's large enough to be a screen
            area = cv2.contourArea(approx)
            if area > image.shape[0] * image.shape[1] * 0.1:  # At least 10% of image
                return order_points(approx.reshape(4, 2))
    
    return None


def order_points(pts: np.ndarray) -> np.ndarray:
    """Order points as: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype=np.float32)
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # Top-left has smallest sum
    rect[2] = pts[np.argmax(s)]  # Bottom-right has largest sum
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # Top-right has smallest difference
    rect[3] = pts[np.argmax(diff)]  # Bottom-left has largest difference
    
    return rect


def apply_perspective_correction(image: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """
    Warp the image to correct perspective distortion.
    Corners should be ordered: top-left, top-right, bottom-right, bottom-left.
    """
    (tl, tr, br, bl) = corners
    
    # Calculate dimensions of the corrected image
    width_top = np.linalg.norm(tr - tl)
    width_bottom = np.linalg.norm(br - bl)
    max_width = int(max(width_top, width_bottom))
    
    height_left = np.linalg.norm(bl - tl)
    height_right = np.linalg.norm(br - tr)
    max_height = int(max(height_left, height_right))
    
    # Destination points
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype=np.float32)
    
    # Compute perspective transform and apply
    M = cv2.getPerspectiveTransform(corners, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height))
    
    return warped


def preprocess_image(
    image: np.ndarray,
    apply_perspective: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Full preprocessing pipeline.
    
    Returns:
        Tuple of (processed_grayscale, processed_color)
    """
    processed_color = image.copy()
    
    # Try perspective correction if requested
    if apply_perspective:
        corners = detect_screen_corners(image)
        if corners is not None:
            processed_color = apply_perspective_correction(image, corners)
    
    # Convert to grayscale
    gray = to_grayscale(processed_color)
    
    # Apply blur
    blurred = apply_blur(gray)
    
    # Enhance contrast
    enhanced = enhance_contrast(blurred)
    
    return enhanced, processed_color
