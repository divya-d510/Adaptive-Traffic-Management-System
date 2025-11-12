"""
Camera Management Module
Handles camera initialization and frame capture
"""
import cv2
import numpy as np
from typing import Optional, Tuple
import logging

from app.config import config

logger = logging.getLogger(__name__)


class CameraManager:
    """
    Manages camera operations
    
    Handles camera initialization, configuration, and frame capture
    """
    
    def __init__(self):
        self.camera: Optional[cv2.VideoCapture] = None
        self.is_opened = False
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize camera with configuration"""
        try:
            self.camera = cv2.VideoCapture(config.camera.index)
            
            if self.camera.isOpened():
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.height)
                self.camera.set(cv2.CAP_PROP_FPS, config.camera.fps)
                self.is_opened = True
                logger.info(f"Camera initialized: {config.camera.width}x{config.camera.height} @ {config.camera.fps}fps")
            else:
                logger.warning("Camera not available")
                self.is_opened = False
                
        except Exception as e:
            logger.error(f"Camera initialization error: {e}")
            self.is_opened = False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from camera
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.is_opened or self.camera is None:
            return False, None
        
        try:
            ret, frame = self.camera.read()
            return ret, frame
        except Exception as e:
            logger.error(f"Frame read error: {e}")
            return False, None
    
    def release(self):
        """Release camera resources"""
        if self.camera is not None:
            self.camera.release()
            self.is_opened = False
            logger.info("Camera released")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.release()
