# Scoring System

## Overview

The scoring system implements ISSF (International Shooting Sport Federation) rules for precision rifle shooting.

## Edge Scoring Rule

ISSF uses **edge scoring**: a bullet scores the higher value if any part of the hole touches the scoring ring.

```
scoring_distance = hole_center_distance - bullet_radius
```

This means:
- A bullet that barely touches the 10-ring scores 10
- The effective scoring distance is measured from the bullet's edge, not center

## Score Calculation Flow

```
┌─────────────────┐
│ Detected Hole   │
│ (center_x, y)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Calculate       │
│ Distance (px)   │──── distance = √((x-cx)² + (y-cy)²)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Convert to mm   │──── distance_mm = distance_px / pixels_per_mm
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Apply Edge Rule │──── scoring_distance = distance_mm - bullet_radius_mm
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Find Ring       │──── Compare to ring diameters
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return Score    │──── 10.9 (X), 10, 9, 8, ... 1, or 0 (Miss)
└─────────────────┘
```

## Supported Targets

### 50m Air Rifle (Brazil RS Local)
| Ring | Score | Diameter (mm) |
|------|-------|---------------|
| X | 10.9 | 5.0 |
| 10 | 10 | 10.4 |
| 9 | 9 | 26.4 |
| 8 | 8 | 42.4 |
| 7 | 7 | 58.4 |
| 6 | 6 | 74.4 |
| 5 | 5 | 90.4 |
| 4 | 4 | 106.4 |
| 3 | 3 | 122.4 |
| 2 | 2 | 138.4 |
| 1 | 1 | 154.4 |

**Bullet diameter**: 4.5mm (air rifle pellet)

### ISSF 50m Rifle
Same ring dimensions, but **5.6mm bullet** (.22 LR)

### ISSF 10m Air Rifle
Smaller target (45.5mm total), **4.5mm bullet**

## Decimal Scoring

For finals and tie-breaking, decimal scoring is used:
- **Inner 10 (X-ring)**: 10.9 points
- Each ring can theoretically be subdivided into tenths

## Code Reference

```python
# From scoring.py
def calculate_score(hole, calibration, target_config):
    distance_mm = calculate_distance_mm(hole, calibration)
    scoring_distance = distance_mm - target_config.bullet_radius_mm
    
    for ring in target_config.rings:
        if scoring_distance <= ring.diameter_mm / 2:
            return ScoredHole(score=ring.score, ring_name=ring.name, ...)
    
    return ScoredHole(score=0, ring_name="Miss", ...)
```
