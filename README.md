# Precision Shooting Scorer

Automatic scoring system for precision shooting targets using computer vision.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-orange)

## Features

- 📁 **Image file loading** - Load and score target photos
- � **Camera capture** - Live webcam scoring
- 🎯 **Manual calibration** - Click to set target center and edge
- 📊 **Decimal scoring** - ISSF-compliant 0.0-10.9 scoring
- 🔄 **Auto-detection** - Automatic target and hole detection

## Quick Start

```bash
# Clone and setup
git clone <repository>
cd precision-scorer
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run
python main.py
```

## Usage

### Loading Images
1. Click **📁 Load Image**
2. Click **▶️ Process** for auto-detection
3. View scores in the right panel

### Manual Calibration
For difficult images (monitor photos, off-center targets):
1. Load image
2. Click **🎯 Calibrate**
3. Click target **center**
4. Click outer **ring edge**
5. Click **▶️ Process**

### Camera Mode
1. Switch to **📷 Camera** tab
2. Select camera and click **▶️ Start**
3. Click **📷 Capture** to freeze frame
4. Click **🎯 Process** to score

## Supported Targets

| Target | Bullet | 10-Ring | Config File |
|--------|--------|---------|-------------|
| ISSF 50m Rifle | 5.6mm | 10.4mm | `issf_50m_rifle.json` |
| ISSF 10m Air Rifle | 4.5mm | 0.5mm | `issf_10m_air_rifle.json` |

## Project Structure

```
precision-scorer/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── src/
│   ├── gui.py          # PyQt6 interface
│   ├── detection.py    # Target/hole detection
│   ├── scoring.py      # Score calculation
│   ├── preprocessing.py # Image processing
│   ├── config.py       # Configuration
│   └── capture.py      # Camera handling
├── targets/            # Target JSON configs
└── docs/               # Documentation
```

## Known Limitations

- Monitor/screen photos have lower accuracy
- Overlapping holes may be detected as single hole
- Strong lighting variations affect detection

## Future Plans

- [ ] AI-based detection (Florence-2, YOLOv8)
- [ ] Session history and export
- [ ] Statistics dashboard
- [ ] Multiple target types

## License

MIT
