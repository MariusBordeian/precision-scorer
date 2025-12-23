# Calibration System

## Overview

Calibration establishes the relationship between image pixels and real-world millimeters, enabling accurate scoring.

## Calibration Data

```python
@dataclass
class TargetCalibration:
    center_x: float      # Target center X in pixels
    center_y: float      # Target center Y in pixels
    radius_px: float     # Black area radius in pixels
    pixels_per_mm: float # Conversion factor
```

## Calibration Methods

### 1. Auto-Detection

Uses Hough Circle detection to find the target:

```python
cv2.HoughCircles(
    blurred,
    cv2.HOUGH_GRADIENT,
    dp=1.2,
    minDist=min_dim // 4,
    param1=80,
    param2=40,
    minRadius=min_dim // 10,
    maxRadius=min_dim // 2
)
```

**Pros:**
- No user interaction required
- Works well with clean, centered images

**Cons:**
- Struggles with monitor photos
- May fail on tilted/off-center targets

### 2. Manual Calibration (Recommended)

User clicks two points:
1. **Target center** (bullseye)
2. **Outer ring edge** (black area boundary)

```python
radius = sqrt((edge_x - center_x)² + (edge_y - center_y)²)
pixels_per_mm = (radius * 2) / black_area_diameter_mm
```

**Pros:**
- Works with any image quality
- User controls accuracy
- Essential for monitor/screen photos

**Cons:**
- Requires user interaction

## Coordinate Conversion

The `ClickableImageLabel` widget handles coordinate conversion:

```
Label Click → Pixmap Coords → Original Image Coords
```

1. Account for pixmap centering in QLabel
2. Divide by display scale factor
3. Bounds check against original dimensions

## Usage in Detection

Once calibrated, detection is **masked** to the calibrated area:

```python
# Create mask for calibrated area only
mask = np.zeros(gray_image.shape, dtype=np.uint8)
cv2.circle(mask, (center_x, center_y), radius_px, 255, -1)
masked_gray = cv2.bitwise_and(gray_image, mask)
```

This eliminates false positives outside the target.

## Best Practices

1. **Click the exact center** - accuracy here affects all scores
2. **Click the outer black edge** - not the paper edge
3. **Re-calibrate if image changes** - reload clears calibration
4. **Use manual for difficult images** - monitors, tilted photos, low contrast
