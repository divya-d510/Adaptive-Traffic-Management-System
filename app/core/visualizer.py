"""
Visualization Module
Handles camera feed visualization with overlays
"""
import cv2
import numpy as np
import time
from datetime import datetime
from typing import List, Optional
import logging

from app.core.detector import Detection

logger = logging.getLogger(__name__)


class Visualizer:
    """
    Camera feed visualizer
    
    Adds overlays, bounding boxes, and information to camera frames
    """
    
    @staticmethod
    def draw_detections(frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """
        Draw detection bounding boxes and labels
        
        Args:
            frame: Input frame
            detections: List of detections
            
        Returns:
            Frame with drawn detections
        """
        for detection in detections:
            x, y, w, h = detection.bbox
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
            
            # Draw labels
            cv2.putText(
                frame,
                f"VEHICLE #{detection.id}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )
            
            cv2.putText(
                frame,
                f"Conf: {detection.confidence:.2f}",
                (x, y + h + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1
            )
            
            cv2.putText(
                frame,
                f"Area: {detection.area:.0f}",
                (x, y + h + 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1
            )
            
            # Draw center point
            cv2.circle(frame, detection.center, 5, (255, 0, 0), -1)
        
        return frame
    
    @staticmethod
    def add_info_overlay(
        frame: np.ndarray,
        vehicle_count: int,
        total_contours: int,
        signal_state: str,
        current_phase: str,
        phase_start_time: float,
        total_detections: int,
        signal_changes: int,
        fg_mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Add comprehensive information overlay
        
        Args:
            frame: Input frame
            vehicle_count: Number of vehicles detected
            total_contours: Total contours found
            signal_state: Current signal state
            current_phase: Current traffic phase
            phase_start_time: Phase start timestamp
            total_detections: Total detections count
            signal_changes: Number of signal changes
            fg_mask: Foreground mask (optional)
            
        Returns:
            Frame with overlay
        """
        height, width = frame.shape[:2]
        current_time = datetime.now()
        
        # Create semi-transparent overlay for info panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        
        # Main info panel
        info_lines = [
            f"WEST APPROACH - YOUR CAMERA - {current_time.strftime('%H:%M:%S')}",
            f"Vehicles: {vehicle_count} (from {total_contours} moving objects)",
            f"Signal: {signal_state}",
            f"Phase: {current_phase.replace('_', ' ')}",
            f"Duration: {time.time() - phase_start_time:.1f}s"
        ]
        
        # Signal state colors
        signal_colors = {
            'GREEN': (0, 255, 0),
            'YELLOW': (0, 255, 255),
            'RED': (0, 0, 255)
        }
        
        for i, line in enumerate(info_lines):
            color = signal_colors.get(signal_state, (255, 255, 255)) if "Signal" in line else (255, 255, 255)
            cv2.putText(
                frame,
                line,
                (10, 25 + i * 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )
        
        # Detection zone
        zone_color = (0, 255, 255)
        cv2.rectangle(frame, (30, 160), (width - 30, height - 30), zone_color, 2)
        cv2.putText(
            frame,
            "DETECTION ZONE",
            (40, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            zone_color,
            2
        )
        
        # Movement mask visualization (bottom right)
        if fg_mask is not None:
            mask_size = 120
            mask_resized = cv2.resize(fg_mask, (mask_size, int(mask_size * 0.75)))
            mask_colored = cv2.applyColorMap(mask_resized, cv2.COLORMAP_HOT)
            
            start_y = height - mask_resized.shape[0] - 10
            start_x = width - mask_resized.shape[1] - 10
            
            frame[start_y:start_y + mask_resized.shape[0],
                  start_x:start_x + mask_resized.shape[1]] = mask_colored
            
            cv2.putText(
                frame,
                "MOVEMENT",
                (start_x, start_y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1
            )
        
        # Performance info (bottom left)
        perf_lines = [
            f"Total: {total_detections}",
            f"Changes: {signal_changes}"
        ]
        
        for i, line in enumerate(perf_lines):
            cv2.putText(
                frame,
                line,
                (10, height - 30 + i * 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 0),
                1
            )
        
        # Live indicator
        cv2.circle(frame, (width - 30, 30), 8, (0, 255, 0), -1)
        cv2.putText(
            frame,
            "LIVE",
            (width - 70, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )
        
        return frame
