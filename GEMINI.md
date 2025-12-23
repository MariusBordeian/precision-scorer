# Gemini Instructions

Gemini-specific guidance for this project.

## Project Summary

**Precision Shooting Scorer** - Desktop app using PyQt6 and OpenCV to automatically score shooting targets from images or camera feed.

## Architecture

```
main.py → src/gui.py → src/detection.py → src/scoring.py
                    ↘ src/preprocessing.py
                    ↘ src/config.py (loads targets/*.json)
```

## Current State

### Working
- ✅ Image loading and display
- ✅ Manual calibration (click center + edge)
- ✅ Hole detection with SimpleBlobDetector
- ✅ ISSF decimal scoring
- ✅ Camera capture and processing

### Known Issues
- ⚠️ Monitor/screen photos have detection problems
- ⚠️ Some false positives on ring lines
- ⚠️ Hole clusters may under-count

## Detection Parameters

In `detection.py`, `find_holes_adaptive()`:
```python
minCircularity = 0.55
minConvexity = 0.7
minInertiaRatio = 0.4
min_hole_distance = bullet_radius * 1.5
```

## Future Enhancements

- [ ] AI detection (Florence-2, YOLOv8)
- [ ] Sensitivity slider UI
- [ ] Click-to-remove false positives
- [ ] Session export/history

## Development

```bash
.\venv\Scripts\activate
python main.py
```

Target configs are in `targets/*.json` - add new target types there.
