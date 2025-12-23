# Claude Instructions

Claude-specific guidance for this project.

## Context

This is a **PyQt6 + OpenCV** desktop app for scoring shooting targets. The main challenge is reliable hole detection in varying image conditions.

## Key Areas

### Detection (`src/detection.py`)
- Uses `SimpleBlobDetector` with strict filters
- Manual calibration overrides auto-detection
- Detection is masked to calibrated area only

### GUI (`src/gui.py`)
- `ClickableImageLabel` handles coordinate conversion for calibration clicks
- `ProcessingThread` runs detection in background
- Status bar shows mode (AUTO/MANUAL) and results

## When Making Changes

1. **Test with multiple image types** - Paper targets AND monitor photos
2. **Preserve manual calibration** - It's the key fallback for difficult images
3. **Keep UI responsive** - Use QThread for processing

## Improvement Opportunities

- Add detection sensitivity slider
- Implement "remove false positive" click mode
- Add Florence-2 or YOLOv8 as alternative detector
- Improve perspective correction for angled photos

## Commands

```bash
# Run
python main.py

# With venv
.\venv\Scripts\python.exe main.py
```
