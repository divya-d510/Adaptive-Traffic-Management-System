"""
CAMERA FEED + WEB DASHBOARD SYSTEM
Shows your live camera feed with detections AND web dashboard simultaneously
Real-time integration between camera view and web interface
"""
import os
import sys
import time
import threading
import cv2
import numpy as np
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import sqlite3
import json

class CameraFeedDashboardSystem:
    """System that shows camera feed AND web dashboard together"""
    
    def __init__(self):
        # Set template folder to parent directory's templates folder
        root_dir = os.path.dirname(os.path.dirname(__file__))
        template_folder = os.path.join(root_dir, 'templates')
        static_folder = os.path.join(root_dir, 'static')
        self.app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
        self.db_path = 'camera_feed_traffic.db'
        
        # Camera system
        self.camera = cv2.VideoCapture(0)
        self.has_camera = self.camera.isOpened()
        
        if self.has_camera:
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            print("✅ Camera connected for dual display")
        else:
            print("❌ Camera not available")
        
        # Vehicle detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, varThreshold=25, history=100
        )
        
        # Detection history for stability
        self.detection_history = []
        self.max_history = 3
        
        # Live data storage
        self.live_data = {
            'intersections': {
                'North': {'vehicles': 0, 'signal': 'RED', 'last_update': datetime.now(), 'queue_length': 0},
                'South': {'vehicles': 0, 'signal': 'RED', 'last_update': datetime.now(), 'queue_length': 0},
                'East': {'vehicles': 0, 'signal': 'GREEN', 'last_update': datetime.now(), 'queue_length': 0},
                'West': {'vehicles': 0, 'signal': 'GREEN', 'last_update': datetime.now(), 'queue_length': 0}  # YOUR CAMERA
            },
            'current_phase': 'East_West_Green',
            'phase_start_time': time.time(),
            'total_detections': 0,
            'signal_changes': 0,
            'latest_frame_info': {
                'timestamp': datetime.now(),
                'detections': [],
                'vehicle_count': 0,
                'processing_fps': 0
            }
        }
        
        # Traffic control
        self.phase_start_time = time.time()
        self.current_phase = 'East_West_Green'
        
        # Threading
        self.camera_thread = None
        self.running = False
        
        self.setup_database()
        self.setup_routes()
        
        print("🎥 Camera Feed + Dashboard System Initialized")
        print("📹 Dual display: Camera feed + Web dashboard")
    
    def setup_database(self):
        """Setup database for logging"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS camera_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    vehicle_count INTEGER NOT NULL,
                    detection_details TEXT,
                    signal_state TEXT NOT NULL,
                    phase_info TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signal_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    event_type TEXT NOT NULL,
                    from_phase TEXT,
                    to_phase TEXT,
                    trigger_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Database setup for camera feed system")
            
        except Exception as e:
            print(f"❌ Database setup error: {e}")
    
    def detect_and_visualize_vehicles(self, frame):
        """Detect vehicles and create visualization for camera feed"""
        if frame is None:
            return 0, frame, []
        
        # Create display frame
        display_frame = frame.copy()
        height, width = frame.shape[:2]
        
        # Background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        
        # Clean up mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        vehicle_count = 0
        detections = []
        valid_detections = []
        
        # Process detections
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            
            if 200 < area < 15000:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                if 0.3 < aspect_ratio < 4.0:
                    vehicle_count += 1
                    confidence = min(0.95, area / 8000.0)
                    
                    detection_info = {
                        'id': i+1,
                        'bbox': (x, y, w, h),
                        'confidence': confidence,
                        'area': area,
                        'center': (x + w//2, y + h//2)
                    }
                    
                    detections.append(detection_info)
                    valid_detections.append(detection_info)
                    
                    # Draw detection on display frame
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                    
                    # Add labels
                    cv2.putText(display_frame, f"VEHICLE #{i+1}", (x, y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(display_frame, f"Conf: {confidence:.2f}", (x, y + h + 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    cv2.putText(display_frame, f"Area: {area:.0f}", (x, y + h + 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    # Draw center point
                    center = (x + w//2, y + h//2)
                    cv2.circle(display_frame, center, 5, (255, 0, 0), -1)
        
        # Stabilize count using history
        self.detection_history.append(vehicle_count)
        if len(self.detection_history) > self.max_history:
            self.detection_history.pop(0)
        
        stable_count = int(np.mean(self.detection_history))
        
        # Add comprehensive overlay
        self.add_camera_overlay(display_frame, stable_count, len(contours), fg_mask, valid_detections)
        
        return stable_count, display_frame, valid_detections
    
    def add_camera_overlay(self, frame, vehicle_count, total_contours, fg_mask, detections):
        """Add comprehensive overlay to camera frame"""
        height, width = frame.shape[:2]
        current_time = datetime.now()
        
        # Create semi-transparent overlay for info panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        
        # Main info panel
        info_lines = [
            f"🎥 WEST APPROACH - YOUR CAMERA - {current_time.strftime('%H:%M:%S')}",
            f"🚗 Vehicles Detected: {vehicle_count} (from {total_contours} moving objects)",
            f"🚦 Signal State: {self.live_data['intersections']['West']['signal']}",
            f"📊 Current Phase: {self.current_phase.replace('_', ' ')}",
            f"⏱️ Phase Duration: {time.time() - self.phase_start_time:.1f}s"
        ]
        
        # Signal state color
        signal_colors = {'GREEN': (0, 255, 0), 'YELLOW': (0, 255, 255), 'RED': (0, 0, 255)}
        
        for i, line in enumerate(info_lines):
            if "Signal State" in line:
                color = signal_colors.get(self.live_data['intersections']['West']['signal'], (255, 255, 255))
            else:
                color = (255, 255, 255)
            
            cv2.putText(frame, line, (10, 25 + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Detection zone
        zone_color = (0, 255, 255)
        cv2.rectangle(frame, (30, 160), (width-30, height-30), zone_color, 2)
        cv2.putText(frame, "DETECTION ZONE", (40, 180), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, zone_color, 2)
        
        # Movement mask visualization (bottom right)
        if fg_mask is not None:
            mask_size = 120
            mask_resized = cv2.resize(fg_mask, (mask_size, int(mask_size * 0.75)))
            mask_colored = cv2.applyColorMap(mask_resized, cv2.COLORMAP_HOT)
            
            start_y = height - mask_resized.shape[0] - 10
            start_x = width - mask_resized.shape[1] - 10
            
            frame[start_y:start_y + mask_resized.shape[0], 
                  start_x:start_x + mask_resized.shape[1]] = mask_colored
            
            cv2.putText(frame, "MOVEMENT", (start_x, start_y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Performance info (bottom left)
        fps = len(self.detection_history) / max(1, len(self.detection_history) * 0.1)
        perf_lines = [
            f"FPS: {fps:.1f}",
            f"Total: {self.live_data['total_detections']}",
            f"Changes: {self.live_data['signal_changes']}"
        ]
        
        for i, line in enumerate(perf_lines):
            cv2.putText(frame, line, (10, height - 50 + i * 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        # Live connection indicator
        cv2.circle(frame, (width - 30, 30), 8, (0, 255, 0), -1)
        cv2.putText(frame, "LIVE", (width - 70, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    def simulate_other_intersections(self):
        """Simulate other intersections"""
        current_time = time.time()
        
        patterns = {
            'North': 2 + 3 * np.sin(current_time * 0.2),
            'South': 3 + 2 * np.sin(current_time * 0.2 + 1),
            'East': 4 + 1 * np.sin(current_time * 0.15)
        }
        
        for direction in ['North', 'South', 'East']:
            base_count = max(0, int(patterns[direction] + np.random.randint(-1, 2)))
            
            # Traffic clearing
            if self.live_data['intersections'][direction]['signal'] == 'GREEN':
                phase_duration = current_time - self.phase_start_time
                if phase_duration > 8:
                    clearing = max(0.1, 1.0 - (phase_duration - 8) / 20)
                    base_count = int(base_count * clearing)
            
            self.live_data['intersections'][direction]['vehicles'] = base_count
            self.live_data['intersections'][direction]['queue_length'] = base_count * 1.2
            self.live_data['intersections'][direction]['last_update'] = datetime.now()
    
    def update_traffic_signals(self):
        """Update traffic signals with logging"""
        current_time = time.time()
        phase_duration = current_time - self.phase_start_time
        
        if self.current_phase == 'East_West_Green':
            current_vehicles = (self.live_data['intersections']['East']['vehicles'] + 
                              self.live_data['intersections']['West']['vehicles'])
            waiting_vehicles = (self.live_data['intersections']['North']['vehicles'] + 
                              self.live_data['intersections']['South']['vehicles'])
            
            calculated_duration = max(6, min(15, 8 + current_vehicles * 1))
            
            should_change = (phase_duration >= calculated_duration or 
                           (current_vehicles == 0 and waiting_vehicles > 0 and phase_duration >= 6))
            
            if should_change:
                self.change_phase('North_South_Green', 
                                f"EW: {current_vehicles} vehicles, NS: {waiting_vehicles} waiting")
        
        elif self.current_phase == 'North_South_Green':
            current_vehicles = (self.live_data['intersections']['North']['vehicles'] + 
                              self.live_data['intersections']['South']['vehicles'])
            waiting_vehicles = (self.live_data['intersections']['East']['vehicles'] + 
                              self.live_data['intersections']['West']['vehicles'])
            
            calculated_duration = max(6, min(15, 8 + current_vehicles * 1))
            
            should_change = (phase_duration >= calculated_duration or 
                           (current_vehicles == 0 and waiting_vehicles > 0 and phase_duration >= 6))
            
            if should_change:
                self.change_phase('East_West_Green', 
                                f"NS: {current_vehicles} vehicles, EW: {waiting_vehicles} waiting")
    
    def change_phase(self, new_phase, reason):
        """Change traffic signal phase with database logging"""
        old_phase = self.current_phase
        self.current_phase = new_phase
        self.phase_start_time = time.time()
        self.live_data['signal_changes'] += 1
        
        # Update signal states
        if new_phase == 'East_West_Green':
            self.live_data['intersections']['East']['signal'] = 'GREEN'
            self.live_data['intersections']['West']['signal'] = 'GREEN'
            self.live_data['intersections']['North']['signal'] = 'RED'
            self.live_data['intersections']['South']['signal'] = 'RED'
        else:
            self.live_data['intersections']['East']['signal'] = 'RED'
            self.live_data['intersections']['West']['signal'] = 'RED'
            self.live_data['intersections']['North']['signal'] = 'GREEN'
            self.live_data['intersections']['South']['signal'] = 'GREEN'
        
        # Log to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            trigger_data = json.dumps({
                'vehicle_counts': {d: self.live_data['intersections'][d]['vehicles'] 
                                 for d in self.live_data['intersections']},
                'reason': reason
            })
            
            cursor.execute('''
                INSERT INTO signal_events (timestamp, event_type, from_phase, to_phase, trigger_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now(), 'phase_change', old_phase, new_phase, trigger_data))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Signal logging error: {e}")
        
        print(f"🚦 SIGNAL CHANGE: {old_phase} → {new_phase} ({reason})")
    
    def camera_processing_loop(self):
        """Main camera processing with visualization"""
        print("📹 Starting camera processing with visual feed...")
        
        # Create camera window
        cv2.namedWindow('Live Camera Feed - West Approach', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Live Camera Feed - West Approach', 800, 600)
        
        while self.running:
            try:
                if self.has_camera:
                    ret, frame = self.camera.read()
                    if ret:
                        # Detect and visualize vehicles
                        vehicle_count, display_frame, detections = self.detect_and_visualize_vehicles(frame)
                        
                        # Update live data
                        self.live_data['intersections']['West']['vehicles'] = vehicle_count
                        self.live_data['intersections']['West']['last_update'] = datetime.now()
                        self.live_data['total_detections'] += vehicle_count
                        
                        # Update frame info for web dashboard
                        self.live_data['latest_frame_info'] = {
                            'timestamp': datetime.now(),
                            'detections': detections,
                            'vehicle_count': vehicle_count,
                            'processing_fps': 10  # Approximate
                        }
                        
                        # Show camera feed
                        cv2.imshow('Live Camera Feed - West Approach', display_frame)
                        
                        # Log detection to database
                        if vehicle_count > 0:
                            self.log_camera_detection(vehicle_count, detections)
                
                # Simulate other intersections
                self.simulate_other_intersections()
                
                # Update traffic control
                self.update_traffic_signals()
                
                # Handle window events
                key = cv2.waitKey(50) & 0xFF
                if key == ord('q'):
                    print("👋 Camera feed closed")
                    break
                
            except Exception as e:
                print(f"Camera processing error: {e}")
                time.sleep(1)
        
        cv2.destroyAllWindows()
    
    def log_camera_detection(self, vehicle_count, detections):
        """Log camera detection to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            detection_details = json.dumps({
                'count': vehicle_count,
                'detections': [
                    {
                        'id': d['id'],
                        'confidence': d['confidence'],
                        'area': d['area']
                    } for d in detections
                ]
            })
            
            phase_info = json.dumps({
                'current_phase': self.current_phase,
                'phase_duration': time.time() - self.phase_start_time
            })
            
            cursor.execute('''
                INSERT INTO camera_detections 
                (timestamp, vehicle_count, detection_details, signal_state, phase_info)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now(), vehicle_count, detection_details, 
                  self.live_data['intersections']['West']['signal'], phase_info))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Detection logging error: {e}")
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('camera_dashboard.html')
        
        @self.app.route('/api/live-data')
        def live_data():
            return jsonify({
                'intersections': {
                    direction: {
                        'vehicles': data['vehicles'],
                        'signal': data['signal'],
                        'queue_length': data['queue_length'],
                        'last_update': data['last_update'].isoformat()
                    }
                    for direction, data in self.live_data['intersections'].items()
                },
                'current_phase': self.current_phase,
                'phase_duration': time.time() - self.phase_start_time,
                'total_detections': self.live_data['total_detections'],
                'signal_changes': self.live_data['signal_changes'],
                'camera_status': 'active' if self.has_camera else 'inactive',
                'latest_frame_info': {
                    'timestamp': self.live_data['latest_frame_info']['timestamp'].isoformat(),
                    'vehicle_count': self.live_data['latest_frame_info']['vehicle_count'],
                    'detection_count': len(self.live_data['latest_frame_info']['detections']),
                    'processing_fps': self.live_data['latest_frame_info']['processing_fps']
                },
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/camera-detections')
        def camera_detections():
            """Get camera detection history"""
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, vehicle_count, signal_state, phase_info
                    FROM camera_detections 
                    ORDER BY timestamp DESC
                    LIMIT 50
                ''')
                
                rows = cursor.fetchall()
                conn.close()
                
                data = []
                for row in rows:
                    data.append({
                        'timestamp': row[0],
                        'vehicle_count': row[1],
                        'signal_state': row[2],
                        'phase_info': json.loads(row[3]) if row[3] else {}
                    })
                
                return jsonify(data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def start_system(self):
        """Start camera processing"""
        self.running = True
        self.camera_thread = threading.Thread(target=self.camera_processing_loop, daemon=True)
        self.camera_thread.start()
        print("✅ Camera processing started")
    
    def stop_system(self):
        """Stop camera processing"""
        self.running = False
        if self.camera_thread:
            self.camera_thread.join(timeout=2.0)
        if self.has_camera:
            self.camera.release()
        cv2.destroyAllWindows()
        print("⏹️ Camera system stopped")
    
    def run_dual_system(self, host='127.0.0.1', port=5002, debug=False):
        """Run the dual camera feed + web dashboard system"""
        print(f"\n🎥 DUAL SYSTEM: CAMERA FEED + WEB DASHBOARD")
        print("="*80)
        print(f"📹 Camera Feed Window: 'Live Camera Feed - West Approach'")
        print(f"🌐 Web Dashboard: http://{host}:{port}")
        print(f"📊 Database: {self.db_path}")
        print(f"🎯 Features:")
        print(f"   • Live camera feed with vehicle detection visualization")
        print(f"   • Real-time web dashboard with traffic monitoring")
        print(f"   • Dual display: See both camera and dashboard")
        print(f"   • Database logging of all detections and signals")
        print(f"   • Adaptive traffic control based on your camera")
        print("="*80)
        print(f"👉 1. Camera window will open automatically")
        print(f"👉 2. Open http://{host}:{port} in your browser")
        print(f"👉 3. Move in front of camera to see real-time detection!")
        print(f"👉 4. Press 'q' in camera window to close")
        print("="*80)
        
        # Start camera processing
        self.start_system()
        
        try:
            # Run Flask app
            self.app.run(host=host, port=port, debug=debug, use_reloader=False)
        except KeyboardInterrupt:
            print("\n⏹️ System interrupted")
        finally:
            self.stop_system()

def create_camera_dashboard_template():
    """Create camera dashboard template"""
    # Create templates folder in parent directory (project root)
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    os.makedirs(template_dir, exist_ok=True)
    
    template_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Camera Feed + Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .camera-status { 
            animation: pulse 2s infinite; 
            color: #28a745; 
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .detection-count { 
            font-size: 2.5rem; 
            font-weight: bold; 
        }
        .signal-light {
            width: 15px;
            height: 15px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .signal-red { background-color: #dc3545; }
        .signal-green { background-color: #28a745; }
        .camera-direction { 
            border: 3px solid #007bff; 
            background: linear-gradient(45deg, #007bff20, transparent);
        }
        .live-feed-info {
            background: rgba(0, 123, 255, 0.1);
            border-left: 4px solid #007bff;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-video camera-status me-2"></i>
                Camera Feed + Web Dashboard
            </span>
            <div class="text-light">
                <i class="fas fa-circle camera-status me-1"></i>
                <span id="connection-status">CONNECTING...</span>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-3">
        <!-- Camera Feed Status -->
        <div class="row mb-3">
            <div class="col-12">
                <div class="alert live-feed-info">
                    <h5><i class="fas fa-camera me-2"></i>Live Camera Feed Status</h5>
                    <div class="row">
                        <div class="col-md-3">
                            <strong>Camera Window:</strong> <span id="camera-window-status">Check desktop</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Latest Detection:</strong> <span id="latest-detection">--</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Processing FPS:</strong> <span id="processing-fps">--</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Frame Time:</strong> <span id="frame-time">--</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Traffic Status Grid -->
        <div class="row mb-4">
            <div class="col-md-3 mb-3">
                <div class="card">
                    <div class="card-header bg-secondary text-white">
                        <h6><i class="fas fa-compass me-1"></i>North</h6>
                    </div>
                    <div class="card-body text-center p-2">
                        <div class="detection-count" id="north-vehicles">--</div>
                        <small>vehicles</small>
                        <div><span class="signal-light" id="north-signal"></span><span id="north-status">--</span></div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card">
                    <div class="card-header bg-secondary text-white">
                        <h6><i class="fas fa-compass me-1"></i>South</h6>
                    </div>
                    <div class="card-body text-center p-2">
                        <div class="detection-count" id="south-vehicles">--</div>
                        <small>vehicles</small>
                        <div><span class="signal-light" id="south-signal"></span><span id="south-status">--</span></div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card">
                    <div class="card-header bg-secondary text-white">
                        <h6><i class="fas fa-compass me-1"></i>East</h6>
                    </div>
                    <div class="card-body text-center p-2">
                        <div class="detection-count" id="east-vehicles">--</div>
                        <small>vehicles</small>
                        <div><span class="signal-light" id="east-signal"></span><span id="east-status">--</span></div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card camera-direction">
                    <div class="card-header bg-primary text-white">
                        <h6><i class="fas fa-video me-1"></i>West - YOUR CAMERA</h6>
                    </div>
                    <div class="card-body text-center p-2">
                        <div class="detection-count text-primary" id="west-vehicles">--</div>
                        <small>vehicles detected</small>
                        <div><span class="signal-light" id="west-signal"></span><span id="west-status">--</span></div>
                        <small id="west-update">--</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts and Logs -->
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h6>Your Camera Detection History</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="cameraChart" width="400" height="200"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h6>System Information</h6>
                    </div>
                    <div class="card-body">
                        <div class="mb-2">
                            <strong>Current Phase:</strong><br>
                            <span id="current-phase-info">--</span>
                        </div>
                        <div class="mb-2">
                            <strong>Phase Duration:</strong><br>
                            <span id="phase-duration-info">--</span>s
                        </div>
                        <div class="mb-2">
                            <strong>Total Detections:</strong><br>
                            <span id="total-detections-info">--</span>
                        </div>
                        <div class="mb-2">
                            <strong>Signal Changes:</strong><br>
                            <span id="signal-changes-info">--</span>
                        </div>
                        <hr>
                        <div class="text-center">
                            <h6>📹 Camera Feed</h6>
                            <p class="small text-muted">Check the camera window on your desktop to see live vehicle detection with bounding boxes and confidence scores!</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let cameraChart;
        
        async function loadLiveData() {
            try {
                const response = await fetch('/api/live-data');
                const data = await response.json();
                
                // Update connection status
                document.getElementById('connection-status').textContent = 
                    `LIVE - ${new Date(data.timestamp).toLocaleTimeString()}`;
                
                // Update camera feed info
                const frameInfo = data.latest_frame_info;
                document.getElementById('latest-detection').textContent = 
                    `${frameInfo.vehicle_count} vehicles`;
                document.getElementById('processing-fps').textContent = 
                    `${frameInfo.processing_fps} FPS`;
                document.getElementById('frame-time').textContent = 
                    new Date(frameInfo.timestamp).toLocaleTimeString();
                
                // Update intersection data
                Object.entries(data.intersections).forEach(([direction, info]) => {
                    const prefix = direction.toLowerCase();
                    
                    document.getElementById(`${prefix}-vehicles`).textContent = info.vehicles;
                    document.getElementById(`${prefix}-status`).textContent = info.signal;
                    
                    const signalLight = document.getElementById(`${prefix}-signal`);
                    signalLight.className = `signal-light signal-${info.signal.toLowerCase()}`;
                    
                    if (direction === 'West') {
                        document.getElementById('west-update').textContent = 
                            new Date(info.last_update).toLocaleTimeString();
                    }
                });
                
                // Update system info
                document.getElementById('current-phase-info').textContent = 
                    data.current_phase.replace('_', ' ');
                document.getElementById('phase-duration-info').textContent = 
                    Math.round(data.phase_duration);
                document.getElementById('total-detections-info').textContent = 
                    data.total_detections;
                document.getElementById('signal-changes-info').textContent = 
                    data.signal_changes;
                
                // Update camera status
                const cameraStatus = data.camera_status === 'active' ? 
                    'Camera window open' : 'Camera not available';
                document.getElementById('camera-window-status').textContent = cameraStatus;
                
            } catch (error) {
                console.error('Error loading live data:', error);
                document.getElementById('connection-status').textContent = 'CONNECTION ERROR';
            }
        }
        
        async function loadCameraChart() {
            try {
                const response = await fetch('/api/camera-detections');
                const data = await response.json();
                
                if (data.length === 0) return;
                
                const ctx = document.getElementById('cameraChart').getContext('2d');
                
                if (cameraChart) {
                    cameraChart.destroy();
                }
                
                const chartData = data.slice(0, 20).reverse();
                
                cameraChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: chartData.map(d => new Date(d.timestamp).toLocaleTimeString()),
                        datasets: [{
                            label: 'Vehicle Detections',
                            data: chartData.map(d => d.vehicle_count),
                            borderColor: 'rgb(0, 123, 255)',
                            backgroundColor: 'rgba(0, 123, 255, 0.1)',
                            tension: 0.1,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Vehicles'
                                }
                            }
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: 'Your Camera - Real-Time Detection History'
                            }
                        }
                    }
                });
                
            } catch (error) {
                console.error('Error loading camera chart:', error);
            }
        }
        
        // Initialize and set up updates
        document.addEventListener('DOMContentLoaded', function() {
            loadLiveData();
            loadCameraChart();
            
            // Real-time updates
            setInterval(loadLiveData, 1000);      // Update every 1 second
            setInterval(loadCameraChart, 8000);   // Update chart every 8 seconds
        });
    </script>
</body>
</html>'''
    
    template_path = os.path.join(template_dir, 'camera_dashboard.html')
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_html)
    
    print(f"✅ Camera dashboard template created at: {template_path}")

def main():
    """Main function"""
    print("🎥 CAMERA FEED + WEB DASHBOARD SYSTEM")
    print("="*60)
    print("Setting up dual display system...")
    
    # Create template
    create_camera_dashboard_template()
    
    # Create and run system
    system = CameraFeedDashboardSystem()
    system.run_dual_system()

if __name__ == "__main__":
    main()