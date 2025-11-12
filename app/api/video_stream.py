"""
Video Streaming
Stream camera and simulation feeds to web browsers
"""
import cv2
import threading
import time
from flask import Response
import logging

logger = logging.getLogger(__name__)


class VideoStreamManager:
    """Manages video streaming for web clients"""
    
    def __init__(self):
        self.camera_frame = None
        self.simulation_frame = None
        self.camera_lock = threading.Lock()
        self.simulation_lock = threading.Lock()
        self.clients = 0
        
    def update_camera_frame(self, frame):
        """Update camera frame for streaming"""
        if frame is not None:
            with self.camera_lock:
                self.camera_frame = frame.copy()
    
    def update_simulation_frame(self, frame):
        """Update simulation frame for streaming"""
        if frame is not None:
            with self.simulation_lock:
                self.simulation_frame = frame.copy()
    
    def get_camera_frame(self):
        """Get latest camera frame"""
        with self.camera_lock:
            return self.camera_frame.copy() if self.camera_frame is not None else None
    
    def get_simulation_frame(self):
        """Get latest simulation frame"""
        with self.simulation_lock:
            return self.simulation_frame.copy() if self.simulation_frame is not None else None
    
    def generate_camera_stream(self):
        """Generate camera video stream"""
        logger.info("Camera stream started")
        self.clients += 1
        
        try:
            while True:
                frame = self.get_camera_frame()
                
                if frame is not None:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    if ret:
                        frame_bytes = buffer.tobytes()
                        
                        # Yield frame in multipart format
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(0.033)  # ~30 FPS
                
        except GeneratorExit:
            logger.info("Camera stream client disconnected")
        finally:
            self.clients -= 1
    
    def generate_simulation_stream(self):
        """Generate simulation video stream"""
        logger.info("Simulation stream started")
        self.clients += 1
        
        try:
            while True:
                frame = self.get_simulation_frame()
                
                if frame is not None:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    if ret:
                        frame_bytes = buffer.tobytes()
                        
                        # Yield frame in multipart format
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(0.033)  # ~30 FPS
                
        except GeneratorExit:
            logger.info("Simulation stream client disconnected")
        finally:
            self.clients -= 1
    
    def get_client_count(self):
        """Get number of connected clients"""
        return self.clients


# Global instance
video_stream_manager = VideoStreamManager()
