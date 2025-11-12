"""
API Routes
RESTful API endpoints for the traffic management system
"""
from flask import Blueprint, jsonify, render_template, Response
from datetime import datetime
import time
import logging
from app.api.video_stream import video_stream_manager

logger = logging.getLogger(__name__)

# Create blueprint
api = Blueprint('api', __name__)

# Global references (will be set by main app)
traffic_controller = None
camera_processor = None
database = None


def init_routes(controller, processor, db):
    """Initialize routes with dependencies"""
    global traffic_controller, camera_processor, database
    traffic_controller = controller
    camera_processor = processor
    database = db


@api.route('/')
def dashboard():
    """Render main dashboard"""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Dashboard render error: {e}")
        return f"Error loading dashboard: {str(e)}", 500


@api.route('/test')
def test_dashboard():
    """Render test dashboard"""
    try:
        return render_template('test_dashboard.html')
    except Exception as e:
        logger.error(f"Test dashboard render error: {e}")
        return f"Error loading test dashboard: {str(e)}", 500


@api.route('/live')
def live_dashboard():
    """Render dashboard with live video streams"""
    try:
        return render_template('dashboard_with_video.html')
    except Exception as e:
        logger.error(f"Live dashboard render error: {e}")
        return f"Error loading live dashboard: {str(e)}", 500


@api.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'camera_status': 'active' if camera_processor and camera_processor.is_running else 'inactive'
    })


@api.route('/api/live-data')
def get_live_data():
    """Get current live data"""
    try:
        if not traffic_controller or not camera_processor:
            return jsonify({'error': 'System not initialized'}), 500
        
        phase_info = traffic_controller.get_phase_info()
        intersection_data = traffic_controller.get_intersection_data()
        
        return jsonify({
            'intersections': intersection_data,
            'current_phase': phase_info['current_phase'],
            'phase_duration': phase_info['phase_duration'],
            'signal_changes': phase_info['signal_changes'],
            'total_detections': camera_processor.total_detections,
            'camera_status': 'active' if camera_processor.is_running else 'inactive',
            'latest_frame_info': {
                'timestamp': camera_processor.latest_frame_info['timestamp'].isoformat(),
                'vehicle_count': camera_processor.latest_frame_info['vehicle_count'],
                'detection_count': len(camera_processor.latest_frame_info['detections']),
                'processing_fps': camera_processor.latest_frame_info['processing_fps']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Live data error: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/api/detections')
def get_detections():
    """Get recent detections"""
    try:
        if not database:
            return jsonify({'error': 'Database not initialized'}), 500
        
        detections = database.get_recent_detections(50)
        return jsonify(detections)
        
    except Exception as e:
        logger.error(f"Detections fetch error: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/api/statistics')
def get_statistics():
    """Get system statistics"""
    try:
        if not database:
            return jsonify({'error': 'Database not initialized'}), 500
        
        stats = database.get_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Statistics fetch error: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/api/config')
def get_config():
    """Get system configuration"""
    from app.config import config
    
    return jsonify({
        'camera': {
            'width': config.camera.width,
            'height': config.camera.height,
            'fps': config.camera.fps
        },
        'traffic': {
            'min_green_time': config.traffic.min_green_time,
            'max_green_time': config.traffic.max_green_time,
            'base_green_time': config.traffic.base_green_time
        },
        'version': config.version
    })


@api.route('/video/camera')
def video_camera():
    """Stream camera feed"""
    return Response(
        video_stream_manager.generate_camera_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@api.route('/video/simulation')
def video_simulation():
    """Stream intersection simulation"""
    return Response(
        video_stream_manager.generate_simulation_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
