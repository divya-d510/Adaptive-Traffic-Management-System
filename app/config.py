"""
Configuration Management
Centralized configuration for the entire system
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class CameraConfig:
    """Camera configuration"""
    index: int = int(os.getenv('CAMERA_INDEX', 0))
    width: int = int(os.getenv('CAMERA_WIDTH', 640))
    height: int = int(os.getenv('CAMERA_HEIGHT', 480))
    fps: int = int(os.getenv('CAMERA_FPS', 30))


@dataclass
class DetectionConfig:
    """Vehicle detection configuration"""
    min_area: int = int(os.getenv('MIN_VEHICLE_AREA', 200))
    max_area: int = int(os.getenv('MAX_VEHICLE_AREA', 15000))
    min_aspect_ratio: float = float(os.getenv('MIN_ASPECT_RATIO', 0.3))
    max_aspect_ratio: float = float(os.getenv('MAX_ASPECT_RATIO', 4.0))
    history_size: int = int(os.getenv('DETECTION_HISTORY_SIZE', 3))
    
    # Background subtraction
    bg_history: int = 100
    bg_var_threshold: int = 25
    bg_detect_shadows: bool = True


@dataclass
class TrafficConfig:
    """Traffic signal configuration"""
    min_green_time: int = int(os.getenv('MIN_GREEN_TIME', 6))
    max_green_time: int = int(os.getenv('MAX_GREEN_TIME', 15))
    base_green_time: int = int(os.getenv('BASE_GREEN_TIME', 8))
    yellow_time: int = 3
    all_red_time: int = 2


@dataclass
class WebConfig:
    """Web server configuration"""
    host: str = os.getenv('WEB_HOST', '0.0.0.0')
    port: int = int(os.getenv('WEB_PORT', 5002))
    debug: bool = os.getenv('DEBUG', 'False').lower() == 'true'


@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str = os.getenv('DB_PATH', 'data/traffic.db')


@dataclass
class Config:
    """Main configuration class"""
    camera: CameraConfig = CameraConfig()
    detection: DetectionConfig = DetectionConfig()
    traffic: TrafficConfig = TrafficConfig()
    web: WebConfig = WebConfig()
    database: DatabaseConfig = DatabaseConfig()
    
    # Application info
    app_name: str = "Traffic Management System"
    version: str = "1.0.0"
    
    def __post_init__(self):
        """Ensure data directory exists"""
        os.makedirs(os.path.dirname(self.database.path), exist_ok=True)


# Global config instance
config = Config()
