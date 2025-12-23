# Detection Pipeline

## Overview

The detection system uses a multi-stage pipeline to identify targets and bullet holes.

## Stage 1: Target Detection

### Hough Circle Detection
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

Finds circular target rings and selects the best candidate based on:
- Distance from image center
- Reasonable size relative to image dimensions

### Fallback Estimation
If Hough detection fails, estimates target at image center with 60% coverage.

## Stage 2: Calibration

The `TargetCalibration` object stores:
- `center_x, center_y`: Target center in pixels
- `radius_px`: Target outer radius in pixels
- `pixels_per_mm`: Conversion factor for scoring

### Manual Calibration
User can override auto-detection by:
1. Clicking target center
2. Clicking outer ring edge

## Stage 3: Hole Detection

### SimpleBlobDetector Parameters
```python
params.filterByArea = True
params.minArea = π × (min_radius)²
params.maxArea = π × (max_radius)²

params.filterByCircularity = True
params.minCircularity = 0.55

params.filterByConvexity = True
params.minConvexity = 0.7

params.filterByInertia = True
params.minInertiaRatio = 0.4
```

### Detection Process
1. Create mask limited to calibrated radius
2. Apply mask to grayscale image
3. Run detector on normal image
4. Run detector on inverted image (catches both dark/light holes)
5. Filter duplicates by minimum distance

## Stage 4: Scoring

Uses ISSF edge-scoring rules:
```
scoring_distance = center_distance - bullet_radius
```

The bullet only needs to touch a ring to score that value.

## Known Limitations

- **Monitor photos**: Low contrast, reflections, and scanlines confuse detection
- **Overlapping holes**: Cluster detection is imperfect
- **Tilted targets**: Perspective distortion affects calibration accuracy

## Future Improvements

- [ ] AI-based detection (Florence-2, YOLOv8)
- [ ] Adaptive parameter tuning
- [ ] User-adjustable sensitivity slider
