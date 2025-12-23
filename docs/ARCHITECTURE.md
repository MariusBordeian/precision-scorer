# Architecture

## Overview

Precision Shooting Scorer is a computer vision application for automatically scoring shooting targets. It uses OpenCV for image processing and PyQt6 for the GUI.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      GUI Layer (PyQt6)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ FileTab  │  │CameraTab │  │ScorePanel│  │MainWindow│    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼──────────┐
│                  Processing Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │preprocessing │  │  detection   │  │   scoring    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────────────┐
│                   Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │    config    │  │   capture    │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Module Descriptions

### `gui.py`
Main GUI components using PyQt6:
- **ClickableImageLabel**: Custom QLabel that emits click coordinates for manual calibration
- **FileTab**: Image file loading and processing with manual calibration support
- **CameraTab**: Webcam capture and processing
- **ScorePanel**: Score display and breakdown
- **ProcessingThread**: Background thread for non-blocking image processing

### `detection.py`
Target and hole detection using OpenCV:
- **detect_target_circles()**: Uses Hough Circles to find target rings
- **detect_target()**: Establishes calibration from detected or estimated target
- **find_holes_adaptive()**: SimpleBlobDetector-based hole detection with strict filters

### `scoring.py`
Score calculation based on ISSF rules:
- **calculate_distance_mm()**: Converts pixel distance to millimeters
- **calculate_score()**: Determines ring score using edge-scoring rules
- **get_score_summary()**: Generates complete scoring breakdown

### `preprocessing.py`
Image preparation:
- **load_image()**: File loading with validation
- **enhance_contrast()**: CLAHE enhancement
- **apply_perspective_correction()**: Optional perspective fix for angled photos

### `config.py`
Target specifications and settings:
- **TargetConfig**: Dataclass holding ring dimensions and bullet size
- **Ring**: Individual ring specification
- Loads target definitions from JSON files

### `capture.py`
Camera handling:
- **CameraCapture**: Webcam discovery, preview, and frame capture

## Data Flow

```
Image Input → Preprocessing → Detection → Scoring → Display
     │              │             │           │         │
     │              ▼             ▼           ▼         ▼
     │         grayscale    calibration   scores    overlay
     │         enhanced      + holes      + rings    image
     │              │             │           │         │
     └──────────────┴─────────────┴───────────┴─────────┘
                              │
                    Manual Calibration
                    (optional override)
```

## Key Design Decisions

1. **SimpleBlobDetector over contours**: More reliable for circular hole detection with built-in filtering
2. **Manual calibration**: Essential fallback for photos of screens/monitors where auto-detection fails
3. **Background threading**: Prevents UI freeze during processing
4. **JSON target configs**: Easy to add new target types without code changes
5. **Masked detection**: Only searches for holes within calibrated area to reduce false positives
