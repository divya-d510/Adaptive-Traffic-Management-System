"""
Intersection Visualizer
Visual simulation of 4-way intersection with animated vehicles
"""
import cv2
import numpy as np
import time
from datetime import datetime
import random


class Vehicle:
    """Represents a vehicle in the simulation"""
    
    def __init__(self, direction, lane, vehicle_id):
        self.direction = direction
        self.lane = lane
        self.id = vehicle_id
        self.color = self.random_vehicle_color()
        self.speed = random.uniform(2, 4)
        self.position = self.get_start_position()
        self.size = (40, 25)  # width, height
        self.stopped = False
        
    def random_vehicle_color(self):
        """Random vehicle colors"""
        colors = [
            (200, 50, 50),   # Blue
            (50, 200, 50),   # Green
            (50, 50, 200),   # Red
            (200, 200, 50),  # Cyan
            (200, 50, 200),  # Magenta
            (100, 100, 100), # Gray
        ]
        return random.choice(colors)
    
    def get_start_position(self):
        """Get starting position based on direction"""
        if self.direction == 'North':
            return [400, 800]  # Bottom, moving up
        elif self.direction == 'South':
            return [400, -50]  # Top, moving down
        elif self.direction == 'East':
            return [-50, 400]  # Left, moving right
        elif self.direction == 'West':
            return [800, 400]  # Right, moving left
        return [0, 0]
    
    def update_position(self, signal_state):
        """Update vehicle position"""
        # Check if should stop at intersection
        intersection_zone = self.get_intersection_zone()
        
        if signal_state == 'RED' and self.in_stop_zone():
            self.stopped = True
        elif signal_state == 'GREEN':
            self.stopped = False
        
        if not self.stopped:
            if self.direction == 'North':
                self.position[1] -= self.speed
            elif self.direction == 'South':
                self.position[1] += self.speed
            elif self.direction == 'East':
                self.position[0] += self.speed
            elif self.direction == 'West':
                self.position[0] -= self.speed
    
    def in_stop_zone(self):
        """Check if vehicle is in stop zone before intersection"""
        x, y = self.position
        
        if self.direction == 'North':
            return 450 < y < 500
        elif self.direction == 'South':
            return 300 < y < 350
        elif self.direction == 'East':
            return 300 < x < 350
        elif self.direction == 'West':
            return 450 < x < 500
        return False
    
    def get_intersection_zone(self):
        """Get intersection zone boundaries"""
        return (300, 300, 500, 500)  # x1, y1, x2, y2
    
    def is_off_screen(self):
        """Check if vehicle is off screen"""
        x, y = self.position
        return x < -100 or x > 900 or y < -100 or y > 900
    
    def draw(self, frame):
        """Draw vehicle on frame"""
        x, y = int(self.position[0]), int(self.position[1])
        w, h = self.size
        
        # Draw vehicle body
        if self.direction in ['North', 'South']:
            cv2.rectangle(frame, (x - w//2, y - h//2), (x + w//2, y + h//2), self.color, -1)
            cv2.rectangle(frame, (x - w//2, y - h//2), (x + w//2, y + h//2), (255, 255, 255), 2)
        else:
            cv2.rectangle(frame, (x - h//2, y - w//2), (x + h//2, y + w//2), self.color, -1)
            cv2.rectangle(frame, (x - h//2, y - w//2), (x + h//2, y + w//2), (255, 255, 255), 2)
        
        # Draw vehicle ID
        cv2.putText(frame, str(self.id), (x - 10, y + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)


class IntersectionVisualizer:
    """Visual simulation of 4-way intersection"""
    
    def __init__(self, width=800, height=800):
        self.width = width
        self.height = height
        self.vehicles = {'North': [], 'South': [], 'East': [], 'West': []}
        self.vehicle_counter = 0
        self.last_spawn_time = {'North': 0, 'South': 0, 'East': 0, 'West': 0}
        self.spawn_interval = 2.0  # seconds
        
        # Traffic signals
        self.signals = {
            'North': 'RED',
            'South': 'RED',
            'East': 'GREEN',
            'West': 'GREEN'
        }
        
    def update_signals(self, signal_data):
        """Update traffic signals from controller"""
        if signal_data:
            for direction, data in signal_data.items():
                if direction in self.signals:
                    self.signals[direction] = data.get('signal', 'RED')
    
    def spawn_vehicle(self, direction, count):
        """Spawn vehicles for a direction"""
        current_time = time.time()
        
        # Spawn based on count
        if current_time - self.last_spawn_time[direction] > self.spawn_interval:
            if count > 0 and len(self.vehicles[direction]) < count + 2:
                self.vehicle_counter += 1
                vehicle = Vehicle(direction, 0, self.vehicle_counter)
                self.vehicles[direction].append(vehicle)
                self.last_spawn_time[direction] = current_time
    
    def update_vehicles(self):
        """Update all vehicles"""
        for direction in self.vehicles:
            signal = self.signals[direction]
            
            # Update each vehicle
            for vehicle in self.vehicles[direction][:]:
                vehicle.update_position(signal)
                
                # Remove off-screen vehicles
                if vehicle.is_off_screen():
                    self.vehicles[direction].remove(vehicle)
    
    def draw_intersection(self, frame):
        """Draw the intersection layout"""
        # Background
        frame[:] = (40, 40, 40)
        
        # Draw roads
        road_color = (60, 60, 60)
        line_color = (200, 200, 100)
        
        # Vertical road (North-South)
        cv2.rectangle(frame, (300, 0), (500, self.height), road_color, -1)
        
        # Horizontal road (East-West)
        cv2.rectangle(frame, (0, 300), (self.width, 500), road_color, -1)
        
        # Center intersection
        cv2.rectangle(frame, (300, 300), (500, 500), (70, 70, 70), -1)
        
        # Lane markings
        for i in range(0, self.height, 40):
            cv2.line(frame, (400, i), (400, i + 20), line_color, 2)
        
        for i in range(0, self.width, 40):
            cv2.line(frame, (i, 400), (i + 20, 400), line_color, 2)
        
        # Stop lines
        stop_line_color = (255, 255, 255)
        cv2.line(frame, (300, 280), (500, 280), stop_line_color, 3)  # North
        cv2.line(frame, (300, 520), (500, 520), stop_line_color, 3)  # South
        cv2.line(frame, (280, 300), (280, 500), stop_line_color, 3)  # East
        cv2.line(frame, (520, 300), (520, 500), stop_line_color, 3)  # West
    
    def draw_traffic_lights(self, frame):
        """Draw traffic lights"""
        light_positions = {
            'North': (350, 250),
            'South': (450, 550),
            'East': (250, 450),
            'West': (550, 350)
        }
        
        for direction, pos in light_positions.items():
            signal = self.signals[direction]
            
            # Light box
            cv2.rectangle(frame, (pos[0] - 15, pos[1] - 40), 
                         (pos[0] + 15, pos[1] + 40), (30, 30, 30), -1)
            cv2.rectangle(frame, (pos[0] - 15, pos[1] - 40), 
                         (pos[0] + 15, pos[1] + 40), (200, 200, 200), 2)
            
            # Red light
            red_color = (0, 0, 255) if signal == 'RED' else (50, 50, 50)
            cv2.circle(frame, (pos[0], pos[1] - 20), 8, red_color, -1)
            
            # Green light
            green_color = (0, 255, 0) if signal == 'GREEN' else (50, 50, 50)
            cv2.circle(frame, (pos[0], pos[1] + 20), 8, green_color, -1)
            
            # Direction label
            cv2.putText(frame, direction[0], (pos[0] - 8, pos[1] + 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    def draw_info_panel(self, frame, vehicle_counts, phase_info):
        """Draw information panel"""
        # Semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Title
        cv2.putText(frame, "INTERSECTION SIMULATION", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Current phase
        phase_text = phase_info.get('current_phase', 'Unknown').replace('_', ' ')
        cv2.putText(frame, f"Phase: {phase_text}", (20, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 200, 255), 1)
        
        # Duration
        duration = phase_info.get('phase_duration', 0)
        cv2.putText(frame, f"Duration: {duration:.1f}s", (20, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 200, 255), 1)
        
        # Vehicle counts
        y_offset = 105
        for direction in ['North', 'South', 'East', 'West']:
            count = vehicle_counts.get(direction, 0)
            signal = self.signals[direction]
            color = (0, 255, 0) if signal == 'GREEN' else (0, 0, 255)
            
            text = f"{direction}: {count} vehicles [{signal}]"
            cv2.putText(frame, text, (20, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
            y_offset += 20
        
        # Timestamp
        timestamp = datetime.now().strftime('%H:%M:%S')
        cv2.putText(frame, timestamp, (20, 190), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
    
    def render_frame(self, vehicle_counts, phase_info):
        """Render a complete frame"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Draw intersection
        self.draw_intersection(frame)
        
        # Draw traffic lights
        self.draw_traffic_lights(frame)
        
        # Spawn and update vehicles
        for direction, count in vehicle_counts.items():
            self.spawn_vehicle(direction, count)
        
        self.update_vehicles()
        
        # Draw all vehicles
        for direction in self.vehicles:
            for vehicle in self.vehicles[direction]:
                vehicle.draw(frame)
        
        # Draw info panel
        self.draw_info_panel(frame, vehicle_counts, phase_info)
        
        return frame
