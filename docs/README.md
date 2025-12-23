# Documentation Index

## Overview

Precision Shooting Scorer - Automatic target scoring using computer vision.

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE](ARCHITECTURE.md) | System overview, module structure, data flow |
| [DETECTION](DETECTION.md) | Hole detection pipeline and parameters |
| [SCORING](SCORING.md) | ISSF scoring rules and calculations |
| [CALIBRATION](CALIBRATION.md) | Auto and manual calibration systems |
| [CONFIGURATION](CONFIGURATION.md) | Target JSON format and API |

## Quick Reference

### Running the App
```bash
cd precision-scorer
.\venv\Scripts\activate
python main.py
```

### Key Files
```
src/
├── gui.py           # UI, calibration UI
├── detection.py     # Hole detection
├── scoring.py       # Score calculation
├── config.py        # Target loading
└── capture.py       # Camera handling

targets/
├── brazil_rs_50m_air.json    # Default
├── issf_50m_rifle.json
└── issf_10m_air_rifle.json
```

### Default Target
**50m Air Rifle (Brazil RS Local)** - 4.5mm bullet, 154.4mm target
