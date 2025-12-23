# Precision Shooting Scorer - Architecture Analysis & Recommendations

## Executive Summary

**Recommendation: Python** for initial development, with optional Rust optimization later for performance-critical components.

### Key Rationale
- **Faster Development**: Python has mature, well-documented computer vision libraries (OpenCV, scikit-image)
- **Cross-Platform**: Works identically on Linux and Windows with minimal effort
- **Easier Debugging**: Interpreted nature allows rapid iteration on image processing algorithms
- **Rich Ecosystem**: Extensive ML/CV libraries and community support
- **Deployment Options**: Can package as standalone executable with PyInstaller for distribution

---

## Problem Analysis

### Target Specifications (50m Air Rifle - Local Competition Format)
Based on the example images and local competition in Rio Grande do Sul, Brazil:
- **Target Diameter**: 154.4mm total (standard 50m rifle target)
- **10-ring**: 10.4mm diameter (innermost, highest score)
- **9-ring**: 26.4mm diameter
- **Pellet Diameter**: 4.5mm (.177 caliber air rifle)
- **Scoring**: Decimal scoring (0.1 point precision) based on distance from center

### Use Cases Identified

1. **Competition Mode**: New pristine target → Score all holes
2. **Practice Mode - Reused Targets**: Target with old holes (some covered with white patches) → Score only NEW black holes
3. **Live Feed Monitoring**: Webcam pointed at electronic display showing target
4. **Post-Event Grading**: Load saved images for scoring

### Technical Challenges

1. **Hole Detection**: Distinguish bullet holes from target rings and background
2. **Old vs New Holes**: Differentiate covered/old holes from fresh ones
3. **Target Calibration**: Automatically detect target center and scale
4. **Perspective Correction**: Handle angled/off-center webcam views
5. **Change Detection**: Identify only newly appeared holes between frames
6. **Precision Measurement**: Calculate distance from center with sub-millimeter accuracy

---

## Recommended Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│  (PyQt6 / Tkinter - live preview, controls, scores)     │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Image Acquisition Layer                     │
│  • Webcam capture (OpenCV)                              │
│  • Image file loader (JPEG/PNG)                         │
│  • Frame comparison / change detection                  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│         Image Preprocessing Pipeline                     │
│  1. Perspective correction (cv2.warpPerspective)        │
│  2. Grayscale conversion                                │
│  3. Noise reduction (Gaussian blur)                     │
│  4. Contrast enhancement (CLAHE)                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│            Target Detection Module                       │
│  • Circular Hough Transform (detect target rings)       │
│  • Template matching (for known target types)           │
│  • Manual calibration fallback (click center + edge)    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│             Hole Detection Module                        │
│  • Adaptive thresholding                                │
│  • Blob detection (cv2.SimpleBlobDetector)              │
│  • Contour analysis (cv2.findContours)                  │
│  • Size/shape filtering (eliminate false positives)     │
│  • Color analysis (black holes vs white patches)        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│          Change Detection Module (Optional)              │
│  • Frame differencing                                   │
│  • Background subtraction                               │
│  • New hole identification                              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Scoring Engine                              │
│  • Distance calculation (Euclidean from center)         │
│  • Ring determination                                   │
│  • Decimal score computation (ISSF rules)               │
│  • Score aggregation and statistics                     │
└─────────────────────────────────────────────────────────┘
```

---

## Technology Stack Recommendations

### Option 1: Python (RECOMMENDED)

#### Core Libraries

| Purpose | Library | Why? |
|---------|---------|------|
| **Computer Vision** | OpenCV (`opencv-python`) | Industry standard, excellent circle/blob detection, mature |
| **Numerical Computing** | NumPy | Fast array operations, required by OpenCV |
| **GUI** | PyQt6 or Tkinter | Cross-platform, native look & feel |
| **Image I/O** | Pillow (PIL) | Image loading, format conversion |
| **Optional: ML** | scikit-learn | If using ML for hole classification |

#### Advantages
- ✅ **Rapid Development**: 3-5x faster than Rust for CV prototypes
- ✅ **Mature Ecosystem**: OpenCV Python bindings are excellent
- ✅ **Easy Debugging**: Print images at each pipeline stage
- ✅ **Cross-Platform**: `pip install` works on Linux/Windows
- ✅ **Community**: Vast CV/ML community support
- ✅ **Deployment**: PyInstaller creates single-file executables

#### Disadvantages
- ❌ **Performance**: ~2-10x slower than native code (but acceptable for this use case)
- ❌ **Distribution Size**: ~100-200MB with dependencies
- ❌ **Startup Time**: 1-2 seconds vs instantaneous

#### Installation
```bash
pip install opencv-python numpy PyQt6 Pillow
```

---

### Option 2: Rust (ALTERNATIVE)

#### Core Libraries

| Purpose | Crate | Notes |
|---------|-------|-------|
| **Computer Vision** | `imageproc`, `opencv-rust` | Less mature than Python OpenCV |
| **Image I/O** | `image` | Good for basic operations |
| **GUI** | `egui`, `iced`, `druid` | Immature compared to PyQt |
| **Numerical** | `ndarray` | NumPy-like arrays |

#### Advantages
- ✅ **Performance**: 2-10x faster than Python
- ✅ **Small Binaries**: 5-20MB statically linked
- ✅ **No Runtime**: Instant startup, no Python installation needed
- ✅ **Type Safety**: Catch bugs at compile time

#### Disadvantages
- ❌ **Development Time**: 3-5x longer due to:
  - Borrow checker complexity
  - Less mature CV libraries
  - Smaller community/examples for CV tasks
- ❌ **OpenCV Bindings**: `opencv-rust` is complex to set up
- ❌ **GUI Ecosystem**: Immature (egui/iced still evolving)
- ❌ **Debugging**: Harder to visualize intermediate images

---

## Recommended Implementation Strategy

### Phase 1: Python Prototype (2-4 weeks)
**Goal**: Prove feasibility, tune algorithms

1. **Static Image Scorer** (Week 1)
   - Load JPEG/PNG images
   - Manual calibration (user clicks center + edge point)
   - Basic hole detection (thresholding + blob detection)
   - Score calculation and display

2. **Automatic Calibration** (Week 2)
   - Hough Circle Transform for target detection
   - Template matching for target center
   - Perspective correction

3. **Old Hole Filtering** (Week 3)
   - Color-based detection (black holes vs white patches)
   - Size filtering (reject too-large patches)
   - Manual hole marking UI (override false positives/negatives)

4. **Webcam Integration** (Week 4)
   - Live camera feed
   - Frame-to-frame change detection
   - Auto-trigger on new hole appearance

### Phase 2: Refinement & Optimization (Optional)
- Add ML-based hole classification (if needed)
- Optimize hot paths (Cython or Rust FFI)
- Package as standalone executable
- Add configuration profiles for different target types

### Phase 3: Rust Port (Optional, if performance needed)
- Only if Python version proves too slow (unlikely)
- Rewrite core image processing in Rust
- Keep GUI in Python with Rust bindings (PyO3)

---

## Detailed Algorithm Recommendations

### 1. Target Detection & Calibration

**Approach**: Hough Circle Transform + Manual Fallback

```python
import cv2
import numpy as np

def detect_target_center(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    
    # Detect circles (target rings)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=100,
        param1=50,
        param2=30,
        minRadius=50,
        maxRadius=500
    )
    
    if circles is not None:
        # Find smallest circle (likely the 10-ring or center)
        circles = circles[0]
        smallest = min(circles, key=lambda c: c[2])  # c[2] is radius
        center = (int(smallest[0]), int(smallest[1]))
        radius = int(smallest[2])
        return center, radius
    else:
        return None, None  # Fallback to manual calibration
```

**Manual Calibration**:
- User clicks target center
- User clicks outer ring edge
- Calculate pixels-per-mm ratio: `scale = measured_pixel_radius / known_mm_radius`

---

### 2. Hole Detection

**Multi-Stage Approach**:

#### Stage 1: Thresholding
```python
def detect_holes(image, center, radius):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Adaptive thresholding (handles lighting variations)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 21, 5
    )
    
    return binary
```

#### Stage 2: Blob Detection
```python
def find_blobs(binary_image):
    # Set up blob detector parameters
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 20  # Minimum hole area in pixels
    params.maxArea = 500  # Maximum (reject large patches)
    params.filterByCircularity = True
    params.minCircularity = 0.5  # Holes should be roughly circular
    
    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(binary_image)
    
    return [(kp.pt[0], kp.pt[1]) for kp in keypoints]
```

#### Stage 3: Old Hole Filtering (Color-Based)
```python
def filter_new_holes(image, hole_candidates):
    new_holes = []
    for (x, y) in hole_candidates:
        # Extract small region around hole
        x, y = int(x), int(y)
        region = image[y-5:y+5, x-5:x+5]
        
        # Calculate average color
        avg_color = np.mean(region, axis=(0, 1))  # BGR
        
        # Black holes have low values, white patches have high values
        brightness = np.mean(avg_color)
        
        if brightness < 100:  # Black hole threshold (tune this)
            new_holes.append((x, y))
    
    return new_holes
```

---

### 3. Scoring Algorithm

**ISSF Decimal Scoring**:

```python
def calculate_score(hole_position, target_center, scale_px_per_mm):
    # Calculate distance from center
    dx = hole_position[0] - target_center[0]
    dy = hole_position[1] - target_center[1]
    distance_px = np.sqrt(dx**2 + dy**2)
    distance_mm = distance_px / scale_px_per_mm
    
    # Adjust for pellet diameter (edge scoring)
    pellet_radius_mm = 4.5 / 2  # Air rifle pellet (.177 cal)
    adjusted_distance_mm = max(0, distance_mm - pellet_radius_mm)
    
    # ISSF 50m rifle ring radii (mm)
    ring_radii = {
        10: 10.4 / 2,   # 5.2mm
        9: 26.4 / 2,    # 13.2mm
        8: 42.4 / 2,    # 21.2mm
        7: 58.4 / 2,    # 29.2mm
        6: 74.4 / 2,    # 37.2mm
        5: 90.4 / 2,    # 45.2mm
        4: 106.4 / 2,   # 53.2mm
        3: 122.4 / 2,   # 61.2mm
        2: 138.4 / 2,   # 69.2mm
        1: 154.4 / 2,   # 77.2mm
    }
    
    # Determine base ring
    base_score = 0
    for score, radius in sorted(ring_radii.items(), reverse=True):
        if adjusted_distance_mm <= radius:
            base_score = score
            break
    
    if base_score == 0:
        return 0.0  # Missed target
    
    # Decimal scoring (0.1 point per mm within ring, roughly)
    # For 10-ring: 10.0 at edge, 10.9 at center (X-ring scoring)
    if base_score == 10:
        # Distance from center of 10-ring in mm
        decimal = max(0.0, 1.0 - (adjusted_distance_mm / ring_radii[10]))
        return 10.0 + (decimal * 0.9)  # 10.0 to 10.9
    else:
        # For other rings, pro-rate within the ring
        ring_width = ring_radii[base_score] - ring_radii.get(base_score + 1, 0)
        distance_into_ring = ring_radii[base_score] - adjusted_distance_mm
        decimal = distance_into_ring / ring_width
        return base_score + min(0.9, decimal)  # Base score + 0.0-0.9
```

---

### 4. Change Detection (for Live Webcam Feed)

**Frame Differencing Approach**:

```python
class ChangeDetector:
    def __init__(self):
        self.previous_frame = None
        self.previous_holes = []
    
    def detect_new_holes(self, current_frame, current_holes):
        if self.previous_frame is None:
            # First frame
            self.previous_frame = current_frame.copy()
            self.previous_holes = current_holes.copy()
            return []
        
        # Compute frame difference
        diff = cv2.absdiff(self.previous_frame, current_frame)
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(diff_gray, 30, 255, cv2.THRESH_BINARY)
        
        # Check which holes are new (appeared in changed regions)
        new_holes = []
        for hole in current_holes:
            x, y = int(hole[0]), int(hole[1])
            if thresh[y, x] > 0:  # Hole in changed region
                # Verify it's not in previous holes list
                is_new = True
                for prev_hole in self.previous_holes:
                    dist = np.sqrt((hole[0]-prev_hole[0])**2 + (hole[1]-prev_hole[1])**2)
                    if dist < 10:  # Within 10 pixels (adjust threshold)
                        is_new = False
                        break
                if is_new:
                    new_holes.append(hole)
        
        # Update state
        self.previous_frame = current_frame.copy()
        self.previous_holes = current_holes.copy()
        
        return new_holes
```

---

## Alternative: "Tiny AI Model" Approach

**When to Consider**:
- Classical CV methods have too many false positives
- Need to handle complex scenarios (torn targets, debris, shadows)

**Recommended Model**: YOLOv8-nano or custom CNN

**Approach**:
1. Collect training dataset (~500-1000 annotated images)
2. Train YOLOv8-nano to detect:
   - Target center
   - Bullet holes (fresh)
   - Patched holes (old)
3. Use model predictions for hole detection

**Pros**:
- Better generalization to varied conditions
- Can distinguish hole types automatically

**Cons**:
- Requires training data collection
- Harder to debug
- Overkill for controlled environment

**Verdict**: **Not recommended initially**. Classical CV is simpler, faster, and sufficient for well-lit, static targets.

---

## Cross-Platform Deployment

### Python Distribution Strategy

#### For End Users (Windows/Linux):
```bash
# Install PyInstaller
pip install pyinstaller

# Create standalone executable
pyinstaller --onefile --windowed \
    --add-data "targets:targets" \
    --name PrecisionScorer \
    main.py
```

This creates:
- **Windows**: `PrecisionScorer.exe` (~150MB)
- **Linux**: `PrecisionScorer` binary (~150MB)

✅ **No Python installation required on target machine**

#### For Developers:
```bash
# requirements.txt
opencv-python==4.8.1.78
numpy==1.24.3
PyQt6==6.6.0
Pillow==10.1.0

# Install
pip install -r requirements.txt
```

---

## Project Structure

```
precision-scorer/
├── main.py                 # Entry point, GUI main window
├── requirements.txt        # Python dependencies
├── README.md              # Setup and usage instructions
│
├── src/
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
│   ├── issf_10m_air_rifle.json
│   └── custom_target.json
│
├── tests/                 # Unit tests
│   ├── test_detection.py
│   └── test_scoring.py
│
└── examples/              # Sample images for testing
    └── *.jpeg
```

---

## Performance Expectations

### Python Implementation

| Task | Expected Performance |
|------|---------------------|
| Static image scoring | 100-500ms per image |
| Webcam live feed | 10-30 FPS (real-time) |
| Hole detection | 10-50ms per frame |
| UI responsiveness | <16ms (60 FPS) |

**Bottlenecks**:
- Hough Circle Transform: ~50-200ms (run once per target)
- Blob detection: ~10-30ms per frame
- GUI rendering: ~5-10ms

**Optimization Strategies** (if needed):
1. **Caching**: Don't re-detect target if camera hasn't moved
2. **ROI Processing**: Only analyze target region, not full frame
3. **Threading**: Offload CV processing to background thread
4. **Downscaling**: Process at 50% resolution, upscale results

---

## Development Timeline Estimate

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| **1. Basic Scorer** | 1 week | Load image, manual calibration, basic hole detection, scoring |
| **2. Auto Calibration** | 3-5 days | Hough circles, automatic target detection |
| **3. Hole Filtering** | 3-5 days | Old hole rejection, color analysis |
| **4. Webcam Integration** | 3-5 days | Live feed, change detection |
| **5. UI Polish** | 3-5 days | Better controls, visualization, settings |
| **6. Testing & Packaging** | 3-5 days | Executable creation, documentation |
| **Total** | **3-4 weeks** | Production-ready application |

---

## Risk Mitigation

| Risk | Impact | Mitigation Strategy |
|------|--------|---------------------|
| **Poor lighting causes false detections** | High | Add brightness/contrast controls, CLAHE preprocessing |
| **Perspective distortion affects accuracy** | Medium | Implement perspective correction, manual calibration fallback |
| **Old holes detected as new** | High | Color-based filtering, manual hole marking UI |
| **Target not auto-detected** | Medium | Provide manual calibration mode (3-click setup) |
| **Performance too slow** | Low | Optimize with threading, ROI processing; Rust rewrite if critical |

---

## Conclusion & Next Steps

### Recommendation Summary
1. **Start with Python** - faster time to working prototype
2. **Use OpenCV + NumPy** - proven, mature, well-documented
3. **Build iteratively** - static images → auto-calibration → webcam
4. **Keep Rust as backup** - only if performance becomes critical bottleneck

### Immediate Next Steps
1. ✅ Review this architecture document
2. Set up Python development environment
3. Implement Phase 1.1: Static image scorer with manual calibration
4. Test on your example images
5. Iterate on hole detection algorithm
6. Add webcam support once static version works well

### Success Criteria
- ✅ Accurately score all holes in pristine targets (competition mode)
- ✅ Filter out old/patched holes (practice mode)
- ✅ Process webcam feed at 10+ FPS
- ✅ Cross-platform (Windows + Linux)
- ✅ Easy to deploy (single executable)

---

**Ready to proceed?** I can start implementing the Phase 1 prototype in Python, or we can discuss any aspects of this architecture first.
