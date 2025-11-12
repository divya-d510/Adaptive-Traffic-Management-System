"""
Camera Processor
Main processing loop for camera feed and detection
"""
import cv2
import threading
import time
from datetime import datetime
from typing import Dict, List
import logging

from app.core.camera import CameraManager
from app.core.detector import VehicleDetector, Detection
from app.core.visualizer import Visualizer
from app.core.intersection_visualizer import IntersectionVisualizer
from app.core.traffic_controller import TrafficController
from app.database import Database
from app.config import config
from app.api.video_stream import video_stream_manager
import numpy as np

logger = logging.getLogger(__name__)


class CameraProcessor:
    """
    Main camera processing system
    
    Coordinates camera capture, detection, visualization, and traffic control
    """
    
    def __init__(self, traffic_controller: TrafficController, database: Database):
        self.traffic_controller = traffic_controller
        self.database = database
        
        # Initialize components
        self.camera = CameraManager()
        self.detector = VehicleDetector()
        self.visualizer = Visualizer()
        self.intersection_viz = IntersectionVisualizer(width=800, height=800)
        
        # State
        self.is_running = False
        self.processing_thread = None
        self.total_detections = 0
        
        # Latest frame info
        self.latest_frame_info = {
            'timestamp': datetime.now(),
            'detections': [],
            'vehicle_count': 0,
            'processing_fps': 0
        }
        
        logger.info("Camera processor initialized")
    
    def process_frame(self, frame):
        """Process a single frame"""
        if frame is None:
            return None
        
        # Detect vehicles
        vehicle_count, detections, fg_mask = self.detector.detect(frame)
        
        # Update traffic controller
        self.traffic_controller.update_vehicle_count('West', vehicle_count)
        
        # Create display frame
        display_frame = frame.copy()
        
        # Draw detections
        display_frame = self.visualizer.draw_detections(display_frame, detections)
        
        # Add info overlay
        phase_info = self.traffic_controller.get_phase_info()
        signal_state = self.traffic_controller.intersections['West']['signal'].value
        
        display_frame = self.visualizer.add_info_overlay(
            display_frame,
            vehicle_count,
            len(detections),
            signal_state,
            phase_info['current_phase'],
            self.traffic_controller.phase_start_time,
            self.total_detections,
            phase_info['signal_changes'],
            fg_mask
        )
        
        # Update stats
        self.total_detections += vehicle_count
        
        # Update latest frame info
        self.latest_frame_info = {
            'timestamp': datetime.now(),
            'detections': [
                {
                    'id': d.id,
                    'confidence': d.confidence,
                    'area': d.area
                }
                for d in detections
            ],
            'vehicle_count': vehicle_count,
            'processing_fps': 10  # Approximate
        }
        
        # Log to database
        if vehicle_count > 0:
            self.database.log_detection(
                vehicle_count,
                self.latest_frame_info['detections'],
                signal_state,
                phase_info
            )
        
        return display_frame
    
    def processing_loop(self):
        """Main processing loop with dual display"""
        logger.info("Starting camera processing loop with intersection simulation")
        
        # Create windows
        camera_window = 'Camera Feed - West Approach'
        sim_window = 'Intersection Simulation - All Directions'
        
        cv2.namedWindow(camera_window, cv2.WINDOW_NORMAL)
        cv2.namedWindow(sim_window, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(camera_window, 800, 600)
        cv2.resizeWindow(sim_window, 800, 800)
        
        # Position windows side by side
        cv2.moveWindow(camera_window, 50, 50)
        cv2.moveWindow(sim_window, 900, 50)
        
        while self.is_running:
            try:
                # Process camera feed
                ret, frame = self.camera.read_frame()
                
                if ret and frame is not None:
                    display_frame = self.process_frame(frame)
                    if display_frame is not None:
                        cv2.imshow(camera_window, display_frame)
                        # Send to web stream
                        video_stream_manager.update_camera_frame(display_frame)
                
                # Update traffic controller
                self.traffic_controller.update()
                
                # Get intersection data for simulation
                intersection_data = self.traffic_controller.get_intersection_data()
                phase_info = self.traffic_controller.get_phase_info()
                
                # Update simulation signals
                self.intersection_viz.update_signals(intersection_data)
                
                # Render intersection simulation
                vehicle_counts = {
                    direction: data['vehicles']
                    for direction, data in intersection_data.items()
                }
                
                sim_frame = self.intersection_viz.render_frame(vehicle_counts, phase_info)
                cv2.imshow(sim_window, sim_frame)
                # Send to web stream
                video_stream_manager.update_simulation_frame(sim_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(50) & 0xFF
                if key == ord('q'):
                    logger.info("User requested shutdown")
                    break
                
            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                time.sleep(1)
        
        cv2.destroyAllWindows()
        logger.info("Camera processing loop stopped")
    
    def start(self):
        """Start camera processing"""
        if self.is_running:
            logger.warning("Processor already running")
            return
        
        self.is_running = True
        self.processing_thread = threading.Thread(
            target=self.processing_loop,
            daemon=True
        )
        self.processing_thread.start()
        logger.info("Camera processor started")
    
    def stop(self):
        """Stop camera processing"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
        self.camera.release()
        logger.info("Camera processor stopped")
