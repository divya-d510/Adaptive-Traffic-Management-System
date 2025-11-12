"""
Vehicle Detection Module
Handles vehicle detection using computer vision
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
import logging

from app.config import config

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Represents a single vehicle detection"""
    id: int
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    area: float
    center: Tuple[int, int]


class VehicleDetector:
    """
    Vehicle detector using background subtraction
    
    Uses MOG2 background subtraction algorithm to detect moving vehicles
    """
    
    def __init__(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=config.detection.bg_detect_shadows,
            varThreshold=config.detection.bg_var_threshold,
            history=config.detection.bg_history
        )
        self.detection_history: List[int] = []
        self.max_history = config.detection.history_size
        logger.info("Vehicle detector initialized")
    
    def detect(self, frame: np.ndarray) -> Tuple[int, List[Detection], Optional[np.ndarray]]:
        """
        Detect vehicles in a frame
        
        Args:
            frame: Input frame from camera
            
        Returns:
            Tuple of (stable_count, detections, foreground_mask)
        """
        if frame is None:
            return 0, [], None
        
        try:
            # Apply background subtraction
            fg_mask = self.bg_subtractor.apply(frame)
            
            # Morphological operations to reduce noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(
                fg_mask, 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Process detections
            detections = []
            vehicle_count = 0
            
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                
                # Filter by area
                if config.detection.min_area < area < config.detection.max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # Filter by aspect ratio
                    if config.detection.min_aspect_ratio < aspect_ratio < config.detection.max_aspect_ratio:
                        vehicle_count += 1
                        confidence = min(0.95, area / 8000.0)
                        
                        detection = Detection(
                            id=i + 1,
                            bbox=(x, y, w, h),
                            confidence=confidence,
                            area=area,
                            center=(x + w // 2, y + h // 2)
                        )
                        detections.append(detection)
            
            # Stabilize count using history
            self.detection_history.append(vehicle_count)
            if len(self.detection_history) > self.max_history:
                self.detection_history.pop(0)
            
            stable_count = int(np.mean(self.detection_history))
            
            return stable_count, detections, fg_mask
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return 0, [], None
    
    def reset(self):
        """Reset detection history"""
        self.detection_history.clear()
        logger.info("Detector reset")
