# Architecture

## Overview

Precision Shooting Scorer is a desktop application for automatically scoring shooting targets using computer vision. Built with **Python 3.10+**, **PyQt6**, and **OpenCV**.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GUI Layer (PyQt6)                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │
│  │ MainWindow │  │  FileTab   │  │ CameraTab  │  │ScorePanel │  │
│  │ + Target   │  │ + Calibr.  │  │ + Preview  │  │ + Summary │  │
│  │   Selector │  │   Mode     │  │   Timer    │  │           │  │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬─────┘  │
└────────┼───────────────┼───────────────┼───────────────┼────────┘
         │               │               │               │
┌────────▼───────────────▼───────────────▼───────────────▼────────┐
│                     Processing Layer                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │ preprocessing  │  │   detection    │  │    scoring     │     │
│  │ - grayscale    │  │ - Hough/Blob   │  │ - edge rules   │     │
│  │ - CLAHE        │  │ - calibration  │  │ - ring lookup  │     │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │     config     │  │    capture     │  │ targets/*.json │     │
│  │ - load targets │  │ - webcam I/O   │  │ - ring specs   │     │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## Module Reference

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `gui.py` | PyQt6 interface | `MainWindow`, `FileTab`, `CameraTab`, `ClickableImageLabel` |
| `detection.py` | Find targets and holes | `detect_target()`, `find_holes_adaptive()` |
| `scoring.py` | Calculate scores | `calculate_score()`, `get_score_summary()` |
| `preprocessing.py` | Image preparation | `preprocess_image()`, `enhance_contrast()` |
| `config.py` | Configuration | `TargetConfig`, `list_available_targets()` |
| `capture.py` | Camera handling | `CameraCapture` |

## Data Flow

```
Image Input
     │
     ▼
┌─────────────┐
│ Preprocess  │ → Grayscale, blur, CLAHE
└─────┬───────┘
      │
      ▼
┌─────────────┐     ┌─────────────┐
│  Calibrate  │ ←── │   Manual    │ (optional override)
│  (auto)     │     │   Clicks    │
└─────┬───────┘     └─────────────┘
      │
      ▼
┌─────────────┐
│   Detect    │ → SimpleBlobDetector on masked area
│   Holes     │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   Score     │ → ISSF edge-scoring rules
│   Holes     │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   Display   │ → Overlay + score panel
└─────────────┘
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **SimpleBlobDetector** | More reliable than contours for circular holes |
| **Manual calibration** | Essential fallback for monitor photos |
| **JSON target configs** | Easy to add new target types |
| **Masked detection** | Reduces false positives outside target |
| **Background threading** | Keeps UI responsive during processing |
| **Brazil RS default** | Local competition requirement |

## Threading Model

```
Main Thread (UI)                    Worker Thread
     │                                    │
     │  ┌──────────────────────────────►  │
     │  │ ProcessingThread.start()        │
     │  │                                 │
     │  │ (image, config, calibration)    ├─► preprocess
     │  │                                 ├─► detect
     │  │                                 ├─► score
     │  │                                 │
     │  │  finished.emit(results) ◄───────┤
     │  └──────────────────────────────►  │
     │                                    │
     ▼  update UI with results            ▼
```

## Related Documentation

- [Detection Pipeline](DETECTION.md)
- [Scoring System](SCORING.md)
- [Calibration](CALIBRATION.md)
- [Configuration](CONFIGURATION.md)
