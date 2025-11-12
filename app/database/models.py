"""
Database Models
SQLite database models and operations
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager
import logging

from app.config import config

logger = logging.getLogger(__name__)


class Database:
    """
    Database manager for traffic system
    
    Handles all database operations including:
    - Detection logging
    - Signal event logging
    - Data retrieval
    """
    
    def __init__(self):
        self.db_path = config.database.path
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database tables"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Camera detections table
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
                
                # Signal events table
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
                
                # System metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def log_detection(
        self,
        vehicle_count: int,
        detections: List[Dict],
        signal_state: str,
        phase_info: Dict
    ):
        """
        Log vehicle detection
        
        Args:
            vehicle_count: Number of vehicles detected
            detections: List of detection details
            signal_state: Current signal state
            phase_info: Current phase information
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                detection_details = json.dumps({
                    'count': vehicle_count,
                    'detections': detections
                })
                
                phase_info_json = json.dumps(phase_info)
                
                cursor.execute('''
                    INSERT INTO camera_detections 
                    (timestamp, vehicle_count, detection_details, signal_state, phase_info)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    vehicle_count,
                    detection_details,
                    signal_state,
                    phase_info_json
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Detection logging error: {e}")
    
    def log_signal_event(
        self,
        event_type: str,
        from_phase: str,
        to_phase: str,
        trigger_data: Dict
    ):
        """
        Log signal event
        
        Args:
            event_type: Type of event
            from_phase: Previous phase
            to_phase: New phase
            trigger_data: Event trigger data
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                trigger_data_json = json.dumps(trigger_data)
                
                cursor.execute('''
                    INSERT INTO signal_events 
                    (timestamp, event_type, from_phase, to_phase, trigger_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    event_type,
                    from_phase,
                    to_phase,
                    trigger_data_json
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Signal event logging error: {e}")
    
    def log_metric(self, metric_name: str, metric_value: float, metadata: Optional[Dict] = None):
        """
        Log system metric
        
        Args:
            metric_name: Name of the metric
            metric_value: Value of the metric
            metadata: Additional metadata
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute('''
                    INSERT INTO system_metrics 
                    (timestamp, metric_name, metric_value, metadata)
                    VALUES (?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    metric_name,
                    metric_value,
                    metadata_json
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Metric logging error: {e}")
    
    def get_recent_detections(self, limit: int = 50) -> List[Dict]:
        """
        Get recent detections
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of detection records
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, vehicle_count, signal_state, phase_info
                    FROM camera_detections 
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                
                return [
                    {
                        'timestamp': row[0],
                        'vehicle_count': row[1],
                        'signal_state': row[2],
                        'phase_info': json.loads(row[3]) if row[3] else {}
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Error fetching detections: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Get system statistics
        
        Returns:
            Dictionary of statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Total detections
                cursor.execute('SELECT COUNT(*) FROM camera_detections')
                total_detections = cursor.fetchone()[0]
                
                # Total signal changes
                cursor.execute('SELECT COUNT(*) FROM signal_events')
                total_signal_changes = cursor.fetchone()[0]
                
                # Average vehicles per detection
                cursor.execute('SELECT AVG(vehicle_count) FROM camera_detections')
                avg_vehicles = cursor.fetchone()[0] or 0
                
                return {
                    'total_detections': total_detections,
                    'total_signal_changes': total_signal_changes,
                    'average_vehicles': round(avg_vehicles, 2)
                }
                
        except Exception as e:
            logger.error(f"Error fetching statistics: {e}")
            return {}
