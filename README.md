# Precision Shooting Scorer

An automated image recognition application for scoring precision shooting targets in championships and training sessions.

## Overview

This application uses computer vision to automatically detect and score bullet holes in shooting targets, supporting both competition mode (pristine targets) and practice mode (reused targets with old holes). It can process static images or live webcam feeds.

## Features

- 🎯 **Automatic Target Detection**: Uses Hough Circle Transform to detect and calibrate target center and scale
- 🔍 **Bullet Hole Detection**: Multi-stage detection pipeline with adaptive thresholding and blob analysis
- 📊 **ISSF Decimal Scoring**: Precise scoring following ISSF 50m rifle standards with 0.1 point accuracy
- 🔄 **Old Hole Filtering**: Distinguishes fresh black holes from covered/patched old holes
- 📹 **Webcam Support**: Real-time scoring from live video feeds with change detection
- 💾 **Image Loading**: Process saved JPEG/PNG images for after-the-fact scoring
- 🖥️ **Cross-Platform**: Runs on both Windows and Linux

## Target Specifications

Supports 50m Air Rifle targets:
- **Target Diameter**: 154.4mm (standard 50m rifle target)
- **10-ring**: 10.4mm diameter
- **Ammunition**: Air rifle pellets (4.5mm / .177 caliber)
- **Scoring**: Decimal scoring (0.0 to 10.9 points)

## Technology Stack

- **Language**: Python 3.8+
- **Computer Vision**: OpenCV (opencv-python)
- **Numerical Computing**: NumPy
- **GUI**: PyQt6
- **Image Processing**: Pillow

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd precision-scorer

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

```bash
pip install opencv-python numpy PyQt6 Pillow
```

## Usage

### Running the Application

```bash
python main.py
```

### Basic Workflow

1. **Load Image or Start Webcam**
   - Click "Load Image" to process a saved target image
   - Click "Start Webcam" for live feed scoring

2. **Calibrate Target**
   - Automatic calibration detects target center and rings
   - Manual calibration: Click center, then click outer edge

3. **Detect Holes**
   - Application automatically detects bullet holes
   - Adjust sensitivity if needed using controls

4. **Review Scores**
   - Individual shot scores displayed
   - Total score and statistics shown
   - Export results if needed

### Modes

#### Competition Mode
- New pristine targets
- Scores all detected holes

#### Practice Mode
- Reused targets with old holes
- Filters out white patches and old holes
- Only scores fresh black holes

## Project Structure

```
precision-scorer/
├── main.py                 # Entry point, GUI main window
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── AGENTS.md              # AI agent collaboration guide
├── CLAUDE.md              # Claude conversation notes
├── GEMINI.md              # Gemini conversation notes
│
├── docs/                  # Documentation
│   └── ARCHITECTURE.md    # Technical architecture details
│
├── src/                   # Source code (to be implemented)
│   ├── __init__.py
│   ├── acquisition.py     # Webcam / image loading
│   ├── preprocessing.py   # Image preprocessing pipeline
│   ├── detection.py       # Target & hole detection
│   ├── scoring.py         # Score calculation
│   ├── calibration.py     # Manual/auto calibration
│   ├── change_detection.py # Frame differencing
│   └── gui.py             # PyQt6 UI components
│
├── targets/               # Target specifications
│   ├── issf_50m_rifle.json
│   └── (other target types)
│
├── tests/                 # Unit tests
│   └── (test files)
│
└── examples/              # Sample images for testing
    └── *.jpeg
```

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed technical architecture, algorithms, and implementation strategy
- **[AGENTS.md](AGENTS.md)** - Guide for AI agent collaboration on this project
- **[CLAUDE.md](CLAUDE.md)** - Notes from Claude conversations
- **[GEMINI.md](GEMINI.md)** - Notes from Gemini conversations

## Development Status

### Completed
- ✅ Architecture analysis and design
- ✅ Technology stack selection
- ✅ Algorithm design for all core components

### In Progress
- 🔄 Implementation Phase 1: Basic static image scorer

### Planned
- 📋 Automatic calibration
- 📋 Webcam integration
- 📋 Change detection for practice mode
- 📋 UI polish and packaging

## Performance Expectations

- **Static Image Scoring**: 100-500ms per image
- **Live Webcam Feed**: 10-30 FPS
- **Hole Detection**: 10-50ms per frame
- **UI Responsiveness**: 60 FPS

## Contributing

This project was developed with assistance from AI coding agents (Claude and Gemini). See [AGENTS.md](AGENTS.md) for collaboration guidelines.

## License

[Choose appropriate license]

## Acknowledgments

- ISSF (International Shooting Sport Federation) for target specifications
- OpenCV community for excellent computer vision tools
- AI assistants (Claude, Gemini) for architecture design and development guidance

## Support

For issues, questions, or contributions, please open an issue on the repository or contact the project maintainers.

---

**Note**: This project is currently in active development. The implementation is being built according to the architecture documented in `docs/ARCHITECTURE.md`.
