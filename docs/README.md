# Camera Feed Traffic Management System

A real-time traffic management system that uses your webcam for vehicle detection and provides a live web dashboard for monitoring traffic flow and adaptive signal control.

![Traffic Management System](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Working-brightgreen)

## ⚡ Quick Commands

```bash
# Install
pip install -r requirements.txt

# Test (optional)
python test_setup.py

# Run (NEW modular version)
python main.py

# Or run old single-file version
python camera_feed_with_dashboard.py

# Then open: http://127.0.0.1:5002
```

## 🚦 Overview

This system provides a working demonstration of adaptive traffic signal control using real-time vehicle detection from your camera. It features both a live camera feed window with visual detection overlays and a web dashboard for monitoring the entire intersection system.

### Key Features

- **🎥 Live Camera Feed**: Real-time vehicle detection with visual bounding boxes and confidence scores
- **🌐 Web Dashboard**: Interactive web interface showing all intersection states
- **�  Adaptive Signals**: Traffic signals adjust based on detected vehicle density
- **� Reael-time Analytics**: Live charts and statistics of traffic flow
- **�  Database Logging**: All detections and signal changes are logged to SQLite
- **� Mtulti-Intersection Simulation**: Simulates a complete 4-way intersection system

## 🏗️ System Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│   Camera Feed       │         │   Web Dashboard      │
│   (OpenCV Window)   │         │   (Flask/Browser)    │
│                     │         │                      │
│ • Vehicle Detection │◄───────►│ • Live Traffic Data  │
│ • Visual Overlays   │         │ • Signal States      │
│ • Bounding Boxes    │         │ • Analytics Charts   │
│ • Confidence Scores │         │ • System Stats       │
└─────────────────────┘         └──────────────────────┘
         │                                   │
         └───────────────┬───────────────────┘
                         │
              ┌──────────────────────┐
              │   SQLite Database    │
              │                      │
              │ • Camera Detections  │
              │ • Signal Events      │
              │ • Traffic Logs       │
              └──────────────────────┘
```

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```
Only 3 packages: opencv-python, numpy, Flask

### Step 2: Test Setup (Optional)
```bash
python test_setup.py
```
Verifies camera access and package installation

### Step 3: Run the System
```bash
python camera_feed_with_dashboard.py
```

### Step 4: View Results
- **Camera window** opens automatically with live detection
- **Web dashboard** at `http://127.0.0.1:5002`
- Move in front of camera to see real-time detection!

**Prerequisites**: Python 3.8+, Webcam, Windows/Linux/Mac

## 📋 Usage

### Camera Feed Window

The OpenCV window shows:
- **Live camera feed** with vehicle detection
- **Bounding boxes** around detected vehicles
- **Confidence scores** for each detection
- **Signal state** (RED/GREEN) for your camera's direction (West)
- **Detection zone** visualization
- **Movement mask** showing motion detection
- **Real-time statistics** (FPS, total detections, signal changes)

Press `q` in the camera window to quit.

### Web Dashboard

Access at `http://127.0.0.1:5002` to see:
- **All 4 intersections** (North, South, East, West)
- **Real-time vehicle counts** for each direction
- **Signal states** with color indicators
- **Detection history chart** showing your camera's detections over time
- **System statistics** (phase duration, total detections, signal changes)
- **Live camera feed status** and processing FPS

### API Endpoints

```bash
# Get live traffic data for all intersections
GET /api/live-data

# Get camera detection history
GET /api/camera-detections
```

## 🔧 How It Works

### Vehicle Detection

The system uses OpenCV's background subtraction (MOG2) to detect moving objects:
1. Captures frames from your webcam
2. Applies background subtraction to identify movement
3. Filters contours by size and aspect ratio to identify vehicles
4. Stabilizes counts using a rolling average
5. Draws bounding boxes and labels on detected vehicles

### Traffic Signal Control

Adaptive signal timing based on vehicle density:
- **Minimum green time**: 6 seconds
- **Maximum green time**: 15 seconds
- **Dynamic adjustment**: Green time extends based on vehicle count
- **Smart switching**: Signals change when no vehicles detected and others are waiting
- **Phase tracking**: System alternates between East-West and North-South green phases

### Database Logging

All events are logged to `camera_feed_traffic.db`:
- **camera_detections**: Vehicle counts, detection details, signal states
- **signal_events**: Phase changes, trigger reasons, vehicle counts

### Customization

You can modify parameters in `camera_feed_with_dashboard.py`:
- Detection sensitivity (area thresholds, aspect ratios)
- Signal timing (min/max green times)
- Camera resolution and FPS
- Detection history window size

## 📊 What You'll See

### Camera Feed Window
- Live video with green bounding boxes around detected vehicles
- Vehicle IDs, confidence scores, and detection areas
- Current signal state (RED/GREEN) for West direction
- Phase information and duration
- Movement visualization mask
- Real-time FPS and statistics

### Web Dashboard
- 4-way intersection grid showing all directions
- Your camera (West) highlighted in blue
- Real-time vehicle counts updating every second
- Signal lights (red/green indicators)
- Detection history chart
- System information panel

### Database
- SQLite database (`camera_feed_traffic.db`) stores:
  - Every vehicle detection with timestamp
  - All signal phase changes
  - Trigger reasons and vehicle counts

## 🎯 Project Structure

### NEW: Modular Architecture
```
traffic-management-system/
├── main.py                          # Main entry point (NEW)
├── config.py                        # Configuration settings
├── database.py                      # Database operations
├── vehicle_detector.py              # Vehicle detection logic
├── visualizer.py                    # Camera visualization
├── traffic_controller.py            # Traffic signal control
├── camera_manager.py                # Camera processing
├── web_server.py                    # Web dashboard & API
├── camera_feed_traffic.db           # SQLite database (auto-created)
├── requirements.txt                 # Python dependencies
├── templates/
│   └── camera_dashboard.html       # Web dashboard template
└── models/
    └── yolov8n.pt                  # YOLOv8 model (optional)
```

### Legacy: Single File (Still Works)
```
├── camera_feed_with_dashboard.py    # Original monolithic version (885 lines)
```

## 🔍 Technical Details

### Dependencies
- **OpenCV**: Camera capture and image processing
- **Flask**: Web server and dashboard
- **NumPy**: Numerical computations
- **SQLite3**: Database storage (built-in with Python)

### Detection Algorithm
- Background subtraction using MOG2
- Morphological operations for noise reduction
- Contour detection and filtering
- Area and aspect ratio validation
- Rolling average for stability

### Performance
- Processes at ~10-30 FPS depending on your hardware
- Low latency detection (<100ms)
- Minimal CPU usage with optimized algorithms
- No GPU required

## 🔧 Troubleshooting

### Camera Not Working
```bash
# Test if camera is accessible
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"
```
- Try changing camera index (0, 1, 2) if you have multiple cameras
- Check if another application is using the camera
- On Linux, ensure you have camera permissions

### Web Dashboard Not Loading
- Ensure Flask is running (check console output)
- Try accessing `http://localhost:5002` instead of `127.0.0.1:5002`
- Check if port 5002 is already in use
- Disable firewall temporarily to test

### No Vehicles Detected
- Ensure there's movement in front of the camera
- Adjust lighting conditions (avoid very dark or very bright)
- The system detects motion, so static objects won't be counted
- Try moving your hand or an object in front of the camera

### Performance Issues
- Lower camera resolution in the code (default is 640x480)
- Reduce FPS setting
- Close other resource-intensive applications
- Ensure adequate lighting for better detection

## 🎓 Learning & Experimentation

This is a demonstration system perfect for:
- Learning computer vision and traffic management concepts
- Understanding adaptive signal control algorithms
- Experimenting with real-time detection systems
- Building portfolio projects
- Educational purposes and research

## 🔮 Future Enhancements

Potential improvements you could add:
- Integration with YOLOv8 for better vehicle detection
- Multiple camera support for different intersections
- Historical data analysis and reporting
- Mobile app for remote monitoring
- Weather condition adaptation
- Pedestrian detection and crosswalk management
- License plate recognition
- Cloud deployment for remote access

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenCV community for computer vision tools
- Flask framework for web development
- Background subtraction algorithms for motion detection

## 📞 Support

For issues or questions:
- Check the troubleshooting section above
- Review the code comments in `camera_feed_with_dashboard.py`
- Experiment with detection parameters for your environment

---

**A simple, working traffic management demonstration system** 🚦