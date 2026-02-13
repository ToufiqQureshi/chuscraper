"""
Human-like behavior simulation for anti-detection.

This module provides utilities to simulate natural human browsing patterns:
- Random delays between actions
- Natural scrolling patterns
- Realistic typing speeds
- Mouse movement simulation
"""

import asyncio
import random
from typing import Optional


class HumanBehavior:
    """Simulate human-like browsing behavior to avoid detection."""
    
    @staticmethod
    async def random_delay(min_sec: float = 1.0, max_sec: float = 3.0) -> None:
        """
        Add a random delay between actions.
        
        Args:
            min_sec: Minimum delay in seconds
            max_sec: Maximum delay in seconds
        """
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
    
    @staticmethod
    async def scroll_naturally(page, direction: str = 'down', speed: str = 'medium') -> None:
        """
        Scroll page naturally with human-like patterns.
        
        Args:
            page: Browser page object
            direction: 'down', 'up', or 'to_bottom'
            speed: 'slow', 'medium', or 'fast'
        """
        # Speed presets
        speeds = {
            'slow': (0.3, 0.7),
            'medium': (0.2, 0.5),
            'fast': (0.1, 0.3)
        }
        delay_range = speeds.get(speed, speeds['medium'])
        
        if direction == 'to_bottom':
            # Scroll to bottom in natural chunks
            viewport_height = await page.evaluate("window.innerHeight")
            total_height = await page.evaluate("document.body.scrollHeight")
            
            current_pos = 0
            while current_pos < total_height:
                # Random scroll distance
                distance = random.randint(int(viewport_height * 0.5), int(viewport_height * 1.2))
                await page.evaluate(f"window.scrollBy(0, {distance})")
                current_pos += distance
                
                # Random pause
                await asyncio.sleep(random.uniform(*delay_range))
                
                # Occasionally scroll back slightly (human-like)
                if random.random() > 0.8:
                    back_distance = random.randint(50, 150)
                    await page.evaluate(f"window.scrollBy(0, -{back_distance})")
                    await asyncio.sleep(random.uniform(0.1, 0.3))
        
        elif direction == 'down':
            # Scroll down in chunks
            scroll_steps = random.randint(3, 7)
            for _ in range(scroll_steps):
                distance = random.randint(100, 400)
                await page.evaluate(f"window.scrollBy(0, {distance})")
                await asyncio.sleep(random.uniform(*delay_range))
        
        elif direction == 'up':
            # Scroll up in chunks
            scroll_steps = random.randint(2, 5)
            for _ in range(scroll_steps):
                distance = random.randint(100, 300)
                await page.evaluate(f"window.scrollBy(0, -{distance})")
                await asyncio.sleep(random.uniform(*delay_range))
        
        # Final small adjustment (very human-like)
        if random.random() > 0.6:
            await page.evaluate(f"window.scrollBy(0, {random.randint(-100, 100)})")
    
    @staticmethod
    async def type_naturally(element, text: str, wpm: int = 120) -> None:
        """
        Type text with human-like speed and variability.
        
        Args:
            element: Input element to type into
            text: Text to type
            wpm: Words per minute (typing speed)
        """
        # Calculate base delay per character
        chars_per_sec = (wpm * 5) / 60  # avg 5 chars per word
        base_delay = 1 / chars_per_sec
        
        for char in text:
            await element.send_keys(char)
            
            # Add variability to typing speed
            delay = base_delay * random.uniform(0.5, 1.5)
            
            # Longer pauses for spaces (natural)
            if char == ' ':
                delay *= random.uniform(1.2, 2.0)
            
            # Occasional longer pauses (thinking)
            if random.random() > 0.9:
                delay *= random.uniform(2.0, 4.0)
            
            await asyncio.sleep(delay)
    
    @staticmethod
    async def mouse_movement_pattern(page, num_moves: int = 5) -> None:
        """
        Simulate random mouse movements on the page.
        
        Args:
            page: Browser page object
            num_moves: Number of random movements
        """
        viewport_width = await page.evaluate("window.innerWidth")
        viewport_height = await page.evaluate("window.innerHeight")
        
        for _ in range(num_moves):
            x = random.randint(0, viewport_width)
            y = random.randint(0, viewport_height)
            
            # Move mouse (via CDP)
            try:
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
            except:
                # Fallback if mouse API not available
                pass
    
    @staticmethod
    async def page_dwell_time(min_sec: float = 5.0, max_sec: float = 15.0) -> None:
        """
        Wait on page to simulate reading/browsing time.
        
        Args:
            min_sec: Minimum dwell time
            max_sec: Maximum dwell time
        """
        dwell_time = random.uniform(min_sec, max_sec)
        await asyncio.sleep(dwell_time)
    
    @classmethod
    async def realistic_page_visit(cls, page, read_content: bool = True) -> None:
        """
        Complete realistic page visit pattern:
        - Initial page load wait
        - Scroll through content
        - Random mouse movements
        - Dwell time
        
        Args:
            page: Browser page object
            read_content: Whether to simulate reading (longer dwell time)
        """
        # Initial load wait
        await cls.random_delay(1, 3)
        
        # Scroll through page
        await cls.scroll_naturally(page, direction='to_bottom', speed='medium')
        
        # Mouse movements
        await cls.mouse_movement_pattern(page, num_moves=random.randint(3, 8))
        
        # Dwell time (reading)
        if read_content:
            await cls.page_dwell_time(5, 15)
        else:
            await cls.random_delay(2, 5)


# Convenience function for quick delays
async def wait_human(min_sec: float = 1.0, max_sec: float = 3.0) -> None:
    """Quick helper for human-like delays."""
    await HumanBehavior.random_delay(min_sec, max_sec)
