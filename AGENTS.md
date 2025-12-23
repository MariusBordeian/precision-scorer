# AI Agent Instructions

This file provides context for AI coding assistants working on this project.

## Project Overview

**Precision Shooting Scorer** is a PyQt6 desktop application for automatically scoring shooting targets using computer vision (OpenCV).

## Tech Stack

- **Python 3.10+**
- **PyQt6** - GUI framework
- **OpenCV (cv2)** - Image processing and detection
- **NumPy** - Array operations

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point |
| `src/gui.py` | All GUI components, threading, calibration |
| `src/detection.py` | Target and hole detection algorithms |
| `src/scoring.py` | ISSF score calculation |
| `src/config.py` | Target config loading |
| `targets/*.json` | Target specifications |

## Common Tasks

### Adding a New Target Type
1. Create JSON in `targets/` with ring diameters
2. Update `config.py` if needed

### Improving Detection
- Modify `find_holes_adaptive()` in `detection.py`
- Adjust SimpleBlobDetector parameters
- Consider adding AI-based detection

### UI Changes
- All in `src/gui.py`
- FileTab handles image loading + manual calibration
- CameraTab handles webcam capture

## Running the App

```bash
cd precision-scorer
.\venv\Scripts\activate
python main.py
```

## Known Issues

1. **Monitor photos** - Low contrast causes detection problems
2. **False positives** - Ring lines sometimes detected as holes
3. **Calibration accuracy** - Manual calibration helps significantly

## Future Work

- Florence-2 or YOLOv8 integration for AI detection
- User-adjustable detection sensitivity
- Session persistence and export
