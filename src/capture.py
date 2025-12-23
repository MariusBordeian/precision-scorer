"""
Camera capture module.
Handles webcam discovery, preview, and frame capture.
"""

import cv2
import numpy as np
from typing import List, Optional


class CameraCapture:
    """Manages webcam capture and preview."""
    
    def __init__(self):
        self._capture: Optional[cv2.VideoCapture] = None
        self._current_index: int = -1
        self._last_frame: Optional[np.ndarray] = None
    
    @staticmethod
    def list_cameras(max_cameras: int = 5) -> List[int]:
        """
        Enumerate available camera indices.
        
        Args:
            max_cameras: Maximum number of indices to check.
            
        Returns:
            List of valid camera indices.
        """
        available = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available
    
    def start(self, camera_index: int, width: int = 1280, height: int = 720) -> bool:
        """
        Start capturing from a camera.
        
        Args:
            camera_index: Index of the camera to use.
            width: Desired frame width.
            height: Desired frame height.
            
        Returns:
            True if camera started successfully.
        """
        self.stop()
        
        self._capture = cv2.VideoCapture(camera_index)
        if not self._capture.isOpened():
            self._capture = None
            return False
        
        # Set resolution
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        self._current_index = camera_index
        return True
    
    def stop(self):
        """Stop the current capture."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
            self._current_index = -1
    
    def is_active(self) -> bool:
        """Check if capture is currently active."""
        return self._capture is not None and self._capture.isOpened()
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read the current frame from the camera.
        
        Returns:
            The current frame as BGR numpy array, or None if unavailable.
        """
        if not self.is_active():
            return None
        
        ret, frame = self._capture.read()
        if ret:
            self._last_frame = frame
            return frame
        return None
    
    def capture_snapshot(self) -> Optional[np.ndarray]:
        """
        Capture the current frame for processing.
        
        Returns:
            A copy of the current frame.
        """
        frame = self.read_frame()
        if frame is not None:
            return frame.copy()
        elif self._last_frame is not None:
            return self._last_frame.copy()
        return None
    
    @property
    def current_camera_index(self) -> int:
        """Get the current camera index."""
        return self._current_index
    
    def __del__(self):
        """Cleanup on destruction."""
        self.stop()
