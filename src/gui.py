"""
PyQt6 GUI for Precision Shooting Scorer.
Provides two input modes: File loading and Camera capture.
Uses background threading for processing to prevent UI freeze.
Supports manual calibration via click-to-set center and radius.
"""

import sys
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QFileDialog, QComboBox,
    QGroupBox, QSplitter, QStatusBar, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings, QPoint
from PyQt6.QtGui import QImage, QPixmap, QMouseEvent

from .config import get_default_target, TargetConfig
from .preprocessing import load_image, preprocess_image
from .detection import detect_all, TargetCalibration, DetectedCircle, find_holes_adaptive
from .scoring import calculate_all_scores, get_score_summary, ScoredHole
from .capture import CameraCapture


class ClickableImageLabel(QLabel):
    """QLabel that emits click positions in image coordinates."""
    clicked = pyqtSignal(int, int)  # x, y in image coordinates
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_size: Optional[Tuple[int, int]] = None  # Original image (width, height)
        self._display_scale: float = 1.0
    
    def set_image_info(self, width: int, height: int, scale: float):
        """Store original image dimensions and scale for coordinate conversion."""
        self._original_size = (width, height)
        self._display_scale = scale
    
    def mousePressEvent(self, event: QMouseEvent):
        if self._original_size is None or self.pixmap() is None:
            return
        
        # Get click position in label coordinates
        click_x = event.position().x()
        click_y = event.position().y()
        
        # Get displayed pixmap size
        pm = self.pixmap()
        pm_w = pm.width()
        pm_h = pm.height()
        
        # Calculate offset (QLabel centers the pixmap by default with AlignCenter)
        label_w = self.width()
        label_h = self.height()
        offset_x = (label_w - pm_w) / 2
        offset_y = (label_h - pm_h) / 2
        
        # Convert to pixmap coordinates
        pm_x = click_x - offset_x
        pm_y = click_y - offset_y
        
        # Check if click is within pixmap bounds
        if pm_x < 0 or pm_x >= pm_w or pm_y < 0 or pm_y >= pm_h:
            return
        
        # Convert pixmap coordinates to original image coordinates
        img_x = int(pm_x / self._display_scale)
        img_y = int(pm_y / self._display_scale)
        
        # Bounds check on original image
        if 0 <= img_x < self._original_size[0] and 0 <= img_y < self._original_size[1]:
            self.clicked.emit(img_x, img_y)


def cv2_to_qpixmap(cv_img: np.ndarray, max_size: int = 700) -> Tuple[QPixmap, float]:
    """Convert OpenCV BGR image to QPixmap. Returns (pixmap, scale_factor)."""
    rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    
    h, w = rgb.shape[:2]
    scale = 1.0
    if w > max_size or h > max_size:
        scale = min(max_size / w, max_size / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        rgb = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
        h, w = new_h, new_w
    
    rgb = rgb.copy()
    bytes_per_line = 3 * w
    qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg.copy()), scale


def draw_detection_overlay(
    image: np.ndarray,
    calibration: Optional[TargetCalibration],
    scored_holes: list[ScoredHole]
) -> np.ndarray:
    """Draw detection results on the image."""
    result = image.copy()
    
    if calibration is not None:
        center = (int(calibration.center_x), int(calibration.center_y))
        cv2.circle(result, center, 8, (0, 255, 0), -1)  # Larger center dot
        cv2.circle(result, center, int(calibration.radius_px), (0, 255, 0), 2)
    
    for scored in scored_holes:
        center = (int(scored.hole.center_x), int(scored.hole.center_y))
        radius = max(5, int(scored.hole.radius))
        
        cv2.circle(result, center, radius, (0, 0, 255), 2)
        
        label = f"{scored.score:.1f}" if scored.score > 0 else "M"
        cv2.putText(
            result, label,
            (center[0] + radius + 5, center[1]),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
        )
    
    return result


def draw_calibration_preview(
    image: np.ndarray,
    center: Optional[Tuple[int, int]],
    radius: Optional[float]
) -> np.ndarray:
    """Draw calibration markers on the image."""
    result = image.copy()
    
    if center is not None:
        cv2.circle(result, center, 10, (0, 255, 255), -1)  # Yellow center
        cv2.circle(result, center, 12, (0, 0, 0), 2)       # Black outline
        
        if radius is not None:
            cv2.circle(result, center, int(radius), (0, 255, 255), 3)  # Yellow radius
            cv2.circle(result, center, int(radius), (0, 0, 0), 1)      # Black outline
    
    return result


class ProcessingThread(QThread):
    """Background thread for image processing."""
    finished = pyqtSignal(object, list, dict, np.ndarray)
    error = pyqtSignal(str)
    
    def __init__(self, image: np.ndarray, target_config: TargetConfig, 
                 manual_calibration: Optional[TargetCalibration] = None):
        super().__init__()
        self.image = image
        self.target_config = target_config
        self.manual_calibration = manual_calibration
    
    def run(self):
        try:
            gray, color = preprocess_image(self.image, apply_perspective=False)
            
            if self.manual_calibration is not None:
                # Use manual calibration
                calibration = self.manual_calibration
                holes = find_holes_adaptive(gray, calibration, self.target_config)
            else:
                # Auto detection
                calibration, holes = detect_all(gray, self.target_config, self.image)
            
            if calibration is None:
                self.error.emit("Could not detect target")
                return
            
            scored = calculate_all_scores(holes, calibration, self.target_config)
            summary = get_score_summary(scored)
            overlay = draw_detection_overlay(self.image, calibration, scored)
            
            self.finished.emit(calibration, scored, summary, overlay)
            
        except Exception as e:
            self.error.emit(str(e))


class FileTab(QWidget):
    """Tab for loading and processing image files with manual calibration support."""
    
    def __init__(self, parent: "MainWindow"):
        super().__init__()
        self.main_window = parent
        self._current_image: Optional[np.ndarray] = None
        self._current_filename: str = ""
        self._processing_thread: Optional[ProcessingThread] = None
        self._settings = QSettings("PrecisionScorer", "App")
        
        # Calibration state
        self._calibration_mode: str = "none"  # "none", "center", "edge"
        self._calib_center: Optional[Tuple[int, int]] = None
        self._calib_radius: Optional[float] = None
        self._manual_calibration: Optional[TargetCalibration] = None
        self._image_scale: float = 1.0
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Top controls row
        controls = QHBoxLayout()
        
        self.load_btn = QPushButton("📁 Load Image")
        self.load_btn.clicked.connect(self._on_load_click)
        controls.addWidget(self.load_btn)
        
        self.calibrate_btn = QPushButton("🎯 Calibrate")
        self.calibrate_btn.clicked.connect(self._on_calibrate_click)
        self.calibrate_btn.setEnabled(False)
        self.calibrate_btn.setToolTip("Click to set target center, then edge")
        controls.addWidget(self.calibrate_btn)
        
        self.clear_calib_btn = QPushButton("❌ Clear")
        self.clear_calib_btn.clicked.connect(self._on_clear_calibration)
        self.clear_calib_btn.setEnabled(False)
        self.clear_calib_btn.setToolTip("Clear manual calibration")
        controls.addWidget(self.clear_calib_btn)
        
        self.process_btn = QPushButton("▶️ Process")
        self.process_btn.clicked.connect(self._on_process_click)
        self.process_btn.setEnabled(False)
        controls.addWidget(self.process_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Calibration status label
        self.calib_status = QLabel("")
        self.calib_status.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.calib_status)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Clickable image display
        self.image_label = ClickableImageLabel()
        self.image_label.setText("Load an image to begin")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background: #f5f5f5;")
        self.image_label.clicked.connect(self._on_image_click)
        layout.addWidget(self.image_label)
    
    def _on_load_click(self):
        last_dir = self._settings.value("last_image_dir", str(Path.home()))
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", last_dir, "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            self._settings.setValue("last_image_dir", str(Path(file_path).parent))
            
            try:
                self._current_image = load_image(file_path)
                self._current_filename = Path(file_path).name
                self._update_image_display()
                
                # Reset calibration
                self._clear_calibration_state()
                
                self.calibrate_btn.setEnabled(True)
                self.process_btn.setEnabled(True)
                self.main_window.status_bar.showMessage(f"Loaded: {self._current_filename}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load image: {e}")
    
    def _update_image_display(self, overlay_image: Optional[np.ndarray] = None):
        """Update the displayed image, optionally with an overlay."""
        if self._current_image is None:
            return
        
        img = overlay_image if overlay_image is not None else self._current_image
        h, w = img.shape[:2]
        
        pixmap, scale = cv2_to_qpixmap(img)
        self._image_scale = scale
        self.image_label.setPixmap(pixmap)
        self.image_label.set_image_info(w, h, scale)
    
    def _on_calibrate_click(self):
        """Start calibration mode."""
        self._calibration_mode = "center"
        self._calib_center = None
        self._calib_radius = None
        self.calib_status.setText("👆 Click on the TARGET CENTER")
        self.calib_status.setStyleSheet("color: #0066cc; font-weight: bold;")
        self.calibrate_btn.setEnabled(False)
        self.process_btn.setEnabled(False)
    
    def _on_clear_calibration(self):
        """Clear manual calibration and revert to auto."""
        self._clear_calibration_state()
        self._update_image_display()
        self.main_window.status_bar.showMessage(f"{self._current_filename} | Calibration cleared - will use auto-detection")
    
    def _clear_calibration_state(self):
        """Reset all calibration state."""
        self._calibration_mode = "none"
        self._calib_center = None
        self._calib_radius = None
        self._manual_calibration = None
        self.clear_calib_btn.setEnabled(False)
        self.calib_status.setText("")
    
    def _on_image_click(self, x: int, y: int):
        """Handle clicks during calibration mode."""
        if self._current_image is None:
            return
        
        if self._calibration_mode == "center":
            # First click: set center
            self._calib_center = (x, y)
            self._calibration_mode = "edge"
            self.calib_status.setText(f"✓ Center set at ({x}, {y}). 👆 Now click on the OUTER RING EDGE")
            
            # Show preview
            preview = draw_calibration_preview(self._current_image, self._calib_center, None)
            self._update_image_display(preview)
            
        elif self._calibration_mode == "edge":
            # Second click: calculate radius
            cx, cy = self._calib_center
            radius = np.sqrt((x - cx)**2 + (y - cy)**2)
            self._calib_radius = radius
            
            # Create calibration object
            target_config = self.main_window.target_config
            pixels_per_mm = (radius * 2) / target_config.black_area_diameter_mm
            
            self._manual_calibration = TargetCalibration(
                center_x=float(cx),
                center_y=float(cy),
                radius_px=float(radius),
                pixels_per_mm=float(pixels_per_mm)
            )
            
            # Show preview
            preview = draw_calibration_preview(self._current_image, self._calib_center, radius)
            self._update_image_display(preview)
            
            # Update UI
            self._calibration_mode = "none"
            self.calib_status.setText(f"✅ Calibration set: center ({cx}, {cy}), radius {radius:.0f}px")
            self.calib_status.setStyleSheet("color: #009900; font-weight: bold;")
            self.calibrate_btn.setEnabled(True)
            self.clear_calib_btn.setEnabled(True)
            self.process_btn.setEnabled(True)
            
            self.main_window.status_bar.showMessage(
                f"{self._current_filename} | Manual calibration set - click Process"
            )
    
    def _on_process_click(self):
        if self._current_image is None:
            return
        
        self.load_btn.setEnabled(False)
        self.calibrate_btn.setEnabled(False)
        self.clear_calib_btn.setEnabled(False)
        self.process_btn.setEnabled(False)
        self.progress.show()
        
        mode = "manual" if self._manual_calibration else "auto"
        self.main_window.status_bar.showMessage(f"Processing ({mode} calibration)...")
        
        self._processing_thread = ProcessingThread(
            self._current_image.copy(),
            self.main_window.target_config,
            self._manual_calibration
        )
        self._processing_thread.finished.connect(self._on_processing_finished)
        self._processing_thread.error.connect(self._on_processing_error)
        self._processing_thread.start()
    
    def _on_processing_finished(self, calibration, scored, summary, overlay):
        self.main_window._last_calibration = calibration
        self.main_window._last_scored_holes = scored
        
        self._update_image_display(overlay)
        self.main_window.score_panel.update_scores(summary)
        
        mode = "manual" if self._manual_calibration else "auto"
        self.main_window.status_bar.showMessage(
            f"{self._current_filename} | {mode.upper()} | Detected {len(scored)} holes - Total: {summary['total']:.1f}"
        )
        
        self._finish_processing()
    
    def _on_processing_error(self, error_msg):
        self.main_window.status_bar.showMessage(f"Error: {error_msg}")
        self.main_window.score_panel.update_scores({"shot_count": 0})
        self._finish_processing()
    
    def _finish_processing(self):
        self.progress.hide()
        self.load_btn.setEnabled(True)
        self.calibrate_btn.setEnabled(True)
        if self._manual_calibration:
            self.clear_calib_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        self._processing_thread = None


class CameraTab(QWidget):
    """Tab for webcam capture."""
    
    def __init__(self, parent: "MainWindow"):
        super().__init__()
        self.main_window = parent
        self.capture = CameraCapture()
        self._preview_timer: Optional[QTimer] = None
        self._captured_frame: Optional[np.ndarray] = None
        self._is_frozen: bool = False
        self._processing_thread: Optional[ProcessingThread] = None
        self._setup_ui()
        QTimer.singleShot(100, self._refresh_cameras)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        controls = QHBoxLayout()
        
        controls.addWidget(QLabel("Camera:"))
        self.camera_combo = QComboBox()
        self.camera_combo.setMinimumWidth(150)
        controls.addWidget(self.camera_combo)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setMaximumWidth(40)
        self.refresh_btn.clicked.connect(self._refresh_cameras)
        controls.addWidget(self.refresh_btn)
        
        self.start_btn = QPushButton("▶️ Start")
        self.start_btn.clicked.connect(self._on_start_click)
        controls.addWidget(self.start_btn)
        
        self.capture_btn = QPushButton("📷 Capture")
        self.capture_btn.clicked.connect(self._on_capture_click)
        self.capture_btn.setEnabled(False)
        controls.addWidget(self.capture_btn)
        
        self.process_btn = QPushButton("🎯 Process")
        self.process_btn.clicked.connect(self._on_process_click)
        self.process_btn.setEnabled(False)
        controls.addWidget(self.process_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)
        
        self.preview_label = QLabel("Select a camera and click Start")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; background: #f5f5f5;")
        layout.addWidget(self.preview_label)
        
        self.captured_group = QGroupBox("Captured Frame")
        captured_layout = QVBoxLayout(self.captured_group)
        self.captured_label = QLabel("No capture yet")
        self.captured_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.captured_label.setMinimumSize(200, 150)
        self.captured_label.setStyleSheet("border: 1px solid #999; background: #e0e0e0;")
        captured_layout.addWidget(self.captured_label)
        self.captured_group.hide()
        layout.addWidget(self.captured_group)
    
    def _refresh_cameras(self):
        self.camera_combo.clear()
        self.main_window.status_bar.showMessage("Scanning for cameras...")
        QApplication.processEvents()
        
        cameras = CameraCapture.list_cameras()
        
        if not cameras:
            self.camera_combo.addItem("No cameras found")
            self.start_btn.setEnabled(False)
        else:
            for idx in cameras:
                self.camera_combo.addItem(f"Camera {idx}", idx)
            self.start_btn.setEnabled(True)
        
        self.main_window.status_bar.showMessage("Ready")
    
    def _on_start_click(self):
        if self.capture.is_active():
            self._stop_preview()
            self.start_btn.setText("▶️ Start")
            self.capture_btn.setEnabled(False)
            self.main_window.status_bar.showMessage("Camera stopped")
        else:
            camera_idx = self.camera_combo.currentData()
            if camera_idx is not None:
                if self.capture.start(camera_idx):
                    self._start_preview()
                    self.start_btn.setText("⏹️ Stop")
                    self.capture_btn.setEnabled(True)
                    self._is_frozen = False
                    self.main_window.status_bar.showMessage(f"Camera {camera_idx} started")
                else:
                    QMessageBox.warning(self, "Error", "Failed to start camera")
    
    def _start_preview(self):
        self._preview_timer = QTimer()
        self._preview_timer.timeout.connect(self._update_preview)
        self._preview_timer.start(33)
    
    def _stop_preview(self):
        if self._preview_timer is not None:
            self._preview_timer.stop()
            self._preview_timer = None
        self.capture.stop()
    
    def _update_preview(self):
        if self._is_frozen:
            return
        frame = self.capture.read_frame()
        if frame is not None:
            pixmap, _ = cv2_to_qpixmap(frame)
            self.preview_label.setPixmap(pixmap)
    
    def _on_capture_click(self):
        self._captured_frame = self.capture.capture_snapshot()
        if self._captured_frame is not None:
            self._is_frozen = True
            self.process_btn.setEnabled(True)
            
            pixmap, _ = cv2_to_qpixmap(self._captured_frame)
            self.preview_label.setPixmap(pixmap)
            
            self.captured_group.show()
            thumb, _ = cv2_to_qpixmap(self._captured_frame, max_size=200)
            self.captured_label.setPixmap(thumb)
            
            self.main_window.status_bar.showMessage("Frame captured - click Process to analyze")
            self.capture_btn.setText("📷 Recapture")
    
    def _on_process_click(self):
        if self._captured_frame is None:
            return
        
        self.capture_btn.setEnabled(False)
        self.process_btn.setEnabled(False)
        self.progress.show()
        self.main_window.status_bar.showMessage("Processing...")
        
        self._processing_thread = ProcessingThread(
            self._captured_frame.copy(),
            self.main_window.target_config
        )
        self._processing_thread.finished.connect(self._on_processing_finished)
        self._processing_thread.error.connect(self._on_processing_error)
        self._processing_thread.start()
    
    def _on_processing_finished(self, calibration, scored, summary, overlay):
        self.main_window._last_calibration = calibration
        self.main_window._last_scored_holes = scored
        
        pixmap, _ = cv2_to_qpixmap(overlay)
        self.preview_label.setPixmap(pixmap)
        self.main_window.score_panel.update_scores(summary)
        self.main_window.status_bar.showMessage(
            f"Detected {len(scored)} holes - Total: {summary['total']:.1f}"
        )
        
        self._finish_processing()
    
    def _on_processing_error(self, error_msg):
        self.main_window.status_bar.showMessage(f"Error: {error_msg}")
        self.main_window.score_panel.update_scores({"shot_count": 0})
        self._finish_processing()
    
    def _finish_processing(self):
        self.progress.hide()
        self.capture_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        self._processing_thread = None
    
    def cleanup(self):
        self._stop_preview()


class ScorePanel(QGroupBox):
    """Panel displaying scoring results."""
    
    def __init__(self):
        super().__init__("Scores")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.total_label = QLabel("Total: -")
        self.total_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.total_label)
        
        self.details_label = QLabel("Load an image and process to see scores")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label)
        
        layout.addStretch()
    
    def update_scores(self, summary: dict):
        if summary["shot_count"] == 0:
            self.total_label.setText("Total: 0")
            self.details_label.setText("No holes detected")
            return
        
        self.total_label.setText(f"Total: {summary['total']:.1f}")
        
        details = f"Shots: {summary['shot_count']}\n"
        details += f"Average: {summary['average']:.2f}\n\n"
        
        for shot in summary["breakdown"]:
            details += f"Shot {shot['shot']}: {shot['score']:.1f} ({shot['ring']})\n"
        
        self.details_label.setText(details)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.target_config = get_default_target()
        self._last_calibration: Optional[TargetCalibration] = None
        self._last_scored_holes: list[ScoredHole] = []
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Precision Shooting Scorer")
        self.setMinimumSize(950, 650)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        self.tabs = QTabWidget()
        self.file_tab = FileTab(self)
        self.camera_tab = CameraTab(self)
        self.tabs.addTab(self.file_tab, "📁 File")
        self.tabs.addTab(self.camera_tab, "📷 Camera")
        splitter.addWidget(self.tabs)
        
        self.score_panel = ScorePanel()
        self.score_panel.setMaximumWidth(250)
        splitter.addWidget(self.score_panel)
        
        splitter.setSizes([700, 250])
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def closeEvent(self, event):
        self.camera_tab.cleanup()
        super().closeEvent(event)


def run_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
