"""
Main Application Entry Point
Traffic Management System
"""
import os
import sys
import logging
from flask import Flask

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.config import config
from app.core.traffic_controller import TrafficController
from app.database import Database
from app.processor import CameraProcessor
from app.api import api, init_routes


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/traffic_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure Flask application"""
    # Create Flask app
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )
    
    # Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Initialize components
    logger.info("Initializing system components...")
    
    database = Database()
    traffic_controller = TrafficController()
    camera_processor = CameraProcessor(traffic_controller, database)
    
    # Initialize API routes
    init_routes(traffic_controller, camera_processor, database)
    
    # Register blueprint
    app.register_blueprint(api)
    
    # Store components in app context
    app.traffic_controller = traffic_controller
    app.camera_processor = camera_processor
    app.database = database
    
    logger.info("System components initialized successfully")
    
    return app


def main():
    """Main function"""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    logger.info("="*80)
    logger.info(f"{config.app_name} v{config.version}")
    logger.info("="*80)
    
    # Create app
    app = create_app()
    
    # Start camera processor
    app.camera_processor.start()
    
    logger.info("")
    logger.info("System Information:")
    logger.info(f"  Camera: {config.camera.width}x{config.camera.height} @ {config.camera.fps}fps")
    logger.info(f"  Web Server: http://{config.web.host}:{config.web.port}")
    logger.info(f"  Database: {config.database.path}")
    logger.info("")
    logger.info("="*80)
    logger.info("System started successfully!")
    logger.info(f"Open your browser to: http://127.0.0.1:{config.web.port}")
    logger.info("Press 'q' in camera window to quit")
    logger.info("="*80)
    logger.info("")
    
    try:
        # Run Flask app
        app.run(
            host=config.web.host,
            port=config.web.port,
            debug=config.web.debug,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("\nShutdown requested...")
    finally:
        app.camera_processor.stop()
        logger.info("System shutdown complete")


if __name__ == '__main__':
    main()
