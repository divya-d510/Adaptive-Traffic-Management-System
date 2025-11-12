"""
Traffic Signal Controller Module
Implements adaptive traffic signal control algorithms
"""
import time
import numpy as np
from datetime import datetime
from typing import Dict, Optional
from enum import Enum
import logging

from app.config import config

logger = logging.getLogger(__name__)


class SignalState(Enum):
    """Traffic signal states"""
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class Phase(Enum):
    """Traffic phases"""
    EAST_WEST_GREEN = "East_West_Green"
    NORTH_SOUTH_GREEN = "North_South_Green"


class TrafficController:
    """
    Adaptive traffic signal controller
    
    Implements intelligent traffic signal control based on:
    - Vehicle density
    - Queue lengths
    - Waiting times
    - Historical patterns
    """
    
    def __init__(self):
        self.current_phase = Phase.EAST_WEST_GREEN
        self.phase_start_time = time.time()
        self.signal_changes = 0
        
        # Initialize intersection data
        self.intersections = {
            'North': {
                'vehicles': 0,
                'signal': SignalState.RED,
                'last_update': datetime.now(),
                'queue_length': 0,
                'waiting_time': 0
            },
            'South': {
                'vehicles': 0,
                'signal': SignalState.RED,
                'last_update': datetime.now(),
                'queue_length': 0,
                'waiting_time': 0
            },
            'East': {
                'vehicles': 0,
                'signal': SignalState.GREEN,
                'last_update': datetime.now(),
                'queue_length': 0,
                'waiting_time': 0
            },
            'West': {
                'vehicles': 0,
                'signal': SignalState.GREEN,
                'last_update': datetime.now(),
                'queue_length': 0,
                'waiting_time': 0
            }
        }
        
        logger.info("Traffic controller initialized")
    
    def update_vehicle_count(self, direction: str, count: int):
        """
        Update vehicle count for a direction
        
        Args:
            direction: Direction name (North, South, East, West)
            count: Number of vehicles detected
        """
        if direction in self.intersections:
            self.intersections[direction]['vehicles'] = count
            self.intersections[direction]['last_update'] = datetime.now()
            self.intersections[direction]['queue_length'] = count * 1.2  # Estimate
    
    def simulate_other_directions(self):
        """Simulate traffic for non-camera directions"""
        current_time = time.time()
        
        # Realistic traffic patterns using sine waves
        patterns = {
            'North': 2 + 3 * np.sin(current_time * 0.2),
            'South': 3 + 2 * np.sin(current_time * 0.2 + 1),
            'East': 4 + 1 * np.sin(current_time * 0.15)
        }
        
        for direction in ['North', 'South', 'East']:
            base_count = max(0, int(patterns[direction] + np.random.randint(-1, 2)))
            
            # Simulate traffic clearing when green
            if self.intersections[direction]['signal'] == SignalState.GREEN:
                phase_duration = current_time - self.phase_start_time
                if phase_duration > 8:
                    # Traffic clears over time
                    clearing_factor = max(0.1, 1.0 - (phase_duration - 8) / 20)
                    base_count = int(base_count * clearing_factor)
            
            self.update_vehicle_count(direction, base_count)
    
    def calculate_optimal_duration(self, vehicle_count: int) -> int:
        """
        Calculate optimal green light duration
        
        Args:
            vehicle_count: Number of vehicles waiting
            
        Returns:
            Optimal duration in seconds
        """
        duration = config.traffic.base_green_time + (vehicle_count * 1)
        return max(
            config.traffic.min_green_time,
            min(config.traffic.max_green_time, duration)
        )
    
    def should_change_phase(self) -> bool:
        """
        Determine if phase should change
        
        Returns:
            True if phase should change
        """
        current_time = time.time()
        phase_duration = current_time - self.phase_start_time
        
        if self.current_phase == Phase.EAST_WEST_GREEN:
            current_vehicles = (
                self.intersections['East']['vehicles'] +
                self.intersections['West']['vehicles']
            )
            waiting_vehicles = (
                self.intersections['North']['vehicles'] +
                self.intersections['South']['vehicles']
            )
            
            optimal_duration = self.calculate_optimal_duration(current_vehicles)
            
            # Change if:
            # 1. Reached optimal duration
            # 2. No current vehicles and others waiting (after min time)
            return (
                phase_duration >= optimal_duration or
                (current_vehicles == 0 and waiting_vehicles > 0 and 
                 phase_duration >= config.traffic.min_green_time)
            )
        
        else:  # NORTH_SOUTH_GREEN
            current_vehicles = (
                self.intersections['North']['vehicles'] +
                self.intersections['South']['vehicles']
            )
            waiting_vehicles = (
                self.intersections['East']['vehicles'] +
                self.intersections['West']['vehicles']
            )
            
            optimal_duration = self.calculate_optimal_duration(current_vehicles)
            
            return (
                phase_duration >= optimal_duration or
                (current_vehicles == 0 and waiting_vehicles > 0 and 
                 phase_duration >= config.traffic.min_green_time)
            )
    
    def change_phase(self, new_phase: Phase, reason: str = ""):
        """
        Change traffic signal phase
        
        Args:
            new_phase: New phase to switch to
            reason: Reason for phase change
        """
        old_phase = self.current_phase
        self.current_phase = new_phase
        self.phase_start_time = time.time()
        self.signal_changes += 1
        
        # Update signal states
        if new_phase == Phase.EAST_WEST_GREEN:
            self.intersections['East']['signal'] = SignalState.GREEN
            self.intersections['West']['signal'] = SignalState.GREEN
            self.intersections['North']['signal'] = SignalState.RED
            self.intersections['South']['signal'] = SignalState.RED
        else:
            self.intersections['East']['signal'] = SignalState.RED
            self.intersections['West']['signal'] = SignalState.RED
            self.intersections['North']['signal'] = SignalState.GREEN
            self.intersections['South']['signal'] = SignalState.GREEN
        
        logger.info(f"Phase change: {old_phase.value} -> {new_phase.value} ({reason})")
    
    def update(self):
        """Update traffic controller state"""
        self.simulate_other_directions()
        
        if self.should_change_phase():
            if self.current_phase == Phase.EAST_WEST_GREEN:
                current = (self.intersections['East']['vehicles'] + 
                          self.intersections['West']['vehicles'])
                waiting = (self.intersections['North']['vehicles'] + 
                          self.intersections['South']['vehicles'])
                reason = f"EW: {current} vehicles, NS: {waiting} waiting"
                self.change_phase(Phase.NORTH_SOUTH_GREEN, reason)
            else:
                current = (self.intersections['North']['vehicles'] + 
                          self.intersections['South']['vehicles'])
                waiting = (self.intersections['East']['vehicles'] + 
                          self.intersections['West']['vehicles'])
                reason = f"NS: {current} vehicles, EW: {waiting} waiting"
                self.change_phase(Phase.EAST_WEST_GREEN, reason)
    
    def get_phase_info(self) -> Dict:
        """Get current phase information"""
        return {
            'current_phase': self.current_phase.value,
            'phase_duration': time.time() - self.phase_start_time,
            'signal_changes': self.signal_changes
        }
    
    def get_intersection_data(self) -> Dict:
        """Get all intersection data"""
        return {
            direction: {
                'vehicles': data['vehicles'],
                'signal': data['signal'].value,
                'queue_length': data['queue_length'],
                'last_update': data['last_update'].isoformat()
            }
            for direction, data in self.intersections.items()
        }
