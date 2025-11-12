# System Architecture

## 📐 Modular Design

The system has been refactored from a single 885-line file into clean, modular components.

## 🏗️ Module Overview

### 1. **main.py** (Entry Point)
- Initializes all components
- Starts camera thread
- Runs web server
- Handles shutdown

**Lines**: ~80

### 2. **config.py** (Configuration)
- All system settings in one place
- Camera parameters
- Detection thresholds
- Signal timing
- Web server settings

**Lines**: ~40

### 3. **database.py** (Data Layer)
- Database setup and management
- Log detections
- Log signal events
- Query detection history

**Lines**: ~130

### 4. **vehicle_detector.py** (Detection Logic)
- Background subtraction
- Contour detection
- Vehicle filtering
- Count stabilization

**Lines**: ~80

### 5. **visualizer.py** (Display)
- Draw bounding boxes
- Add overlays
- Display statistics
- Movement visualization

**Lines**: ~110

### 6. **traffic_controller.py** (Control Logic)
- Signal phase management
- Adaptive timing
- Intersection simulation
- Phase change logic

**Lines**: ~140

### 7. **camera_manager.py** (Camera Processing)
- Camera initialization
- Frame processing
- Detection coordination
- Main processing loop

**Lines**: ~140

### 8. **web_server.py** (Web Interface)
- Flask routes
- API endpoints
- Live data serving
- Dashboard rendering

**Lines**: ~70

## 📊 Comparison

| Aspect | Old (Monolithic) | New (Modular) |
|--------|------------------|---------------|
| **Files** | 1 file | 8 files |
| **Lines per file** | 885 lines | 40-140 lines |
| **Maintainability** | Hard | Easy |
| **Testability** | Difficult | Simple |
| **Reusability** | Low | High |
| **Readability** | Complex | Clear |

## 🔄 Data Flow

```
┌─────────────┐
│   main.py   │  ← Entry point
└──────┬──────┘
       │
       ├──► config.py (settings)
       │
       ├──► database.py (storage)
       │         ▲
       │         │
       ├──► traffic_controller.py
       │         │         ▲
       │         │         │
       ├──► camera_manager.py
       │         │         │
       │         ├──► vehicle_detector.py
       │         │
       │         └──► visualizer.py
       │
       └──► web_server.py
                 │
                 └──► templates/camera_dashboard.html
```

## 🎯 Module Responsibilities

### Separation of Concerns

1. **Configuration** (config.py)
   - Single source of truth for settings
   - Easy to modify parameters
   - No hardcoded values

2. **Data Persistence** (database.py)
   - All database operations isolated
   - Easy to switch databases
   - Consistent logging interface

3. **Detection** (vehicle_detector.py)
   - Pure detection logic
   - No visualization code
   - Reusable in other projects

4. **Visualization** (visualizer.py)
   - All drawing code in one place
   - Easy to customize appearance
   - Independent of detection logic

5. **Control** (traffic_controller.py)
   - Traffic logic isolated
   - Easy to test algorithms
   - No camera dependencies

6. **Camera** (camera_manager.py)
   - Camera operations only
   - Coordinates other modules
   - Clean processing loop

7. **Web** (web_server.py)
   - API endpoints only
   - No business logic
   - Easy to add new routes

## 🧪 Testing Benefits

Each module can now be tested independently:

```python
# Test detector
from vehicle_detector import VehicleDetector
detector = VehicleDetector()
count, detections, mask = detector.detect(test_frame)

# Test controller
from traffic_controller import TrafficController
controller = TrafficController(mock_db)
controller.update_signals()

# Test database
from database import DatabaseManager
db = DatabaseManager(':memory:')  # In-memory for testing
db.log_detection(5, [], 'GREEN', {})
```

## 🔧 Customization

### Easy to Modify

**Change detection parameters:**
```python
# Edit config.py
MIN_VEHICLE_AREA = 300  # Increase minimum size
```

**Add new visualization:**
```python
# Edit visualizer.py
@staticmethod
def add_custom_overlay(frame, data):
    # Your custom visualization
    pass
```

**Implement new control algorithm:**
```python
# Edit traffic_controller.py
def update_signals(self):
    # Your custom algorithm
    pass
```

## 📦 Deployment

### Modular Benefits

1. **Easier debugging** - Isolate issues to specific modules
2. **Parallel development** - Multiple developers can work on different modules
3. **Code reuse** - Use detector in other projects
4. **Testing** - Unit test each module independently
5. **Documentation** - Each module is self-contained

## 🚀 Future Enhancements

With modular architecture, easy to add:

- **New detectors** - Swap vehicle_detector.py with YOLO version
- **Multiple cameras** - Extend camera_manager.py
- **Cloud storage** - Replace database.py with cloud version
- **Mobile app** - Add new API endpoints in web_server.py
- **ML models** - Add new module for predictions

## 📝 Code Quality

### Before (Monolithic)
- ❌ 885 lines in one file
- ❌ Mixed concerns
- ❌ Hard to test
- ❌ Difficult to modify
- ❌ Poor reusability

### After (Modular)
- ✅ 8 focused modules
- ✅ Clear separation
- ✅ Easy to test
- ✅ Simple to modify
- ✅ High reusability

## 🎓 Learning Path

1. Start with **config.py** - Understand settings
2. Read **vehicle_detector.py** - Learn detection
3. Check **visualizer.py** - See visualization
4. Study **traffic_controller.py** - Understand control
5. Review **camera_manager.py** - See coordination
6. Explore **web_server.py** - Learn API
7. Finally **main.py** - See how it all connects

---

**Result**: Clean, maintainable, professional architecture! 🎉
