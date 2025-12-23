# Configuration System

## Target Configuration Files

Target specifications are stored as JSON files in the `targets/` directory.

### File Structure

```json
{
    "name": "50m Air Rifle (Brazil RS Local)",
    "bullet_diameter_mm": 4.5,
    "rings": [
        {"ring": "X", "score": 10.9, "diameter_mm": 5.0},
        {"ring": "10", "score": 10, "diameter_mm": 10.4},
        ...
    ],
    "black_area_diameter_mm": 112.4,
    "total_diameter_mm": 154.4
}
```

### Fields

| Field | Description |
|-------|-------------|
| `name` | Display name in UI |
| `bullet_diameter_mm` | Projectile diameter for edge scoring |
| `rings` | Array of scoring rings (inner to outer) |
| `black_area_diameter_mm` | Used for calibration calculation |
| `total_diameter_mm` | Overall target size |

## Available Targets

| File | Name | Bullet | Use Case |
|------|------|--------|----------|
| `brazil_rs_50m_air.json` | 50m Air Rifle (Brazil RS) | 4.5mm | Local competition default |
| `issf_50m_rifle.json` | ISSF 50m Rifle | 5.6mm | Standard .22 LR |
| `issf_10m_air_rifle.json` | ISSF 10m Air Rifle | 4.5mm | Indoor air rifle |

## Adding New Targets

1. Create a new JSON file in `targets/`
2. Follow the structure above
3. The app will automatically discover it on next launch

### Example: Custom Target

```json
{
    "name": "My Club Target",
    "bullet_diameter_mm": 4.5,
    "rings": [
        {"ring": "10", "score": 10, "diameter_mm": 15.0},
        {"ring": "9", "score": 9, "diameter_mm": 30.0},
        {"ring": "8", "score": 8, "diameter_mm": 45.0}
    ],
    "black_area_diameter_mm": 45.0,
    "total_diameter_mm": 60.0
}
```

## Code API

```python
from config import (
    get_default_target,      # Returns Brazil RS config
    list_available_targets,  # Returns [(name, path), ...]
    load_target,             # Load specific JSON file
    TargetConfig,            # Dataclass for target
    Ring                     # Dataclass for ring
)

# Usage
config = get_default_target()
print(config.name)                    # "50m Air Rifle (Brazil RS Local)"
print(config.bullet_diameter_mm)      # 4.5
print(config.rings[0].score)          # 10.9 (X-ring)
```

## UI Target Selector

The main window includes a dropdown to switch targets at runtime:

1. Select target from dropdown
2. Status bar shows new target and bullet size
3. Re-process image to apply new scoring
