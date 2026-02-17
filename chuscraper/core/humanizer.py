"""
Behavioral Humanization Module for Chuscraper (2026 Edition).

This module provides algorithms to simulate human-like interactions:
1. Bezier Curve Mouse Movements: Replaces linear bot-like paths with natural curves.
2. Typing Cadence: Adds variable delays and rhythm to keystrokes.
"""

import math
import random
import time
from typing import List, Tuple

class Humanizer:
    @staticmethod
    def bezier_curve(
        start_x: int, start_y: int, end_x: int, end_y: int, steps: int = 50
    ) -> List[Tuple[float, float]]:
        """
        Generates a cubic Bezier curve path for mouse movement.
        """
        # Control points (randomized for "human" variation)
        # Deviation controls how "curvy" the path is
        dist = math.hypot(end_x - start_x, end_y - start_y)
        deviation = min(dist / 2, 300) 
        
        # Point 1: 25% to 75% along the path, with random perpendicular offset
        cp1_x = start_x + (end_x - start_x) * random.uniform(0.2, 0.5) + random.uniform(-deviation, deviation)
        cp1_y = start_y + (end_y - start_y) * random.uniform(0.2, 0.5) + random.uniform(-deviation, deviation)
        
        # Point 2: 50% to 80% along the path
        cp2_x = start_x + (end_x - start_x) * random.uniform(0.5, 0.8) + random.uniform(-deviation, deviation)
        cp2_y = start_y + (end_y - start_y) * random.uniform(0.5, 0.8) + random.uniform(-deviation, deviation)

        path = []
        for i in range(steps + 1):
            t = i / steps
            # Cubic Bezier Formula
            x = (1 - t)**3 * start_x + 3 * (1 - t)**2 * t * cp1_x + 3 * (1 - t) * t**2 * cp2_x + t**3 * end_x
            y = (1 - t)**3 * start_y + 3 * (1 - t)**2 * t * cp1_y + 3 * (1 - t) * t**2 * cp2_y + t**3 * end_y
            path.append((x, y))
            
        return path

    @staticmethod
    def typing_cadence(text: str, min_delay: float = 0.05, max_delay: float = 0.15) -> List[Tuple[str, float]]:
        """
        Generates a sequence of (char, delay) for typing simulation.
        Includes periodic longer pauses to simulate "thinking" or "finger travel".
        """
        actions = []
        for i, char in enumerate(text):
            delay = random.uniform(min_delay, max_delay)
            
            # Simulate slight pause after space (word boundary)
            if char == ' ':
                delay += random.uniform(0.05, 0.1)
                
            # Random "hiccups" (thinking pause) every 10-20 chars
            if i > 0 and i % random.randint(10, 20) == 0:
                delay += random.uniform(0.1, 0.3)
                
            actions.append((char, delay))
        return actions

    @staticmethod
    def get_mouse_steps(start_x: int, start_y: int, end_x: int, end_y: int) -> int:
        """
        Calculates realistic number of steps based on distance.
        Fitts's Law approximation: farther targets take longer.
        """
        dist = math.hypot(end_x - start_x, end_y - start_y)
        # Base speed: pixels per step (approx)
        speed = random.uniform(15, 25) 
        steps = max(10, int(dist / speed))
        return steps
