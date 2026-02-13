"""
Rate limiting and concurrency control for safe scraping.

Implements:
- Token bucket rate limiter
- Concurrent request limiter
- Session duration manager
"""

import asyncio
import time
from collections import deque
from typing import Optional
from datetime import datetime, timedelta


class RateLimiter:
    """
    Token bucket rate limiter to prevent excessive requests.
    
    Example:
        limiter = RateLimiter(max_requests=10, time_window=60)
        await limiter.acquire()  # Waits if rate limit exceeded
    """
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Wait until a request slot is available."""
        async with self._lock:
            now = time.time()
            
            # Remove requests outside the time window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest = self.requests[0]
                wait_time = self.time_window - (now - oldest) + 0.1
                
                # Release lock while waiting
                self._lock.release()
                await asyncio.sleep(wait_time)
                self._lock.acquire()
                
                return await self.acquire()
            
            # Record this request
            self.requests.append(now)
    
    def reset(self) -> None:
        """Clear all request history."""
        self.requests.clear()
    
    @property
    def current_rate(self) -> float:
        """Get current requests per second."""
        now = time.time()
        recent = [r for r in self.requests if r > now - self.time_window]
        return len(recent) / self.time_window if recent else 0.0


class ConcurrencyLimiter:
    """
    Limit concurrent operations using semaphore.
    
    Example:
        async with ConcurrencyLimiter(max_concurrent=5):
            # Your concurrent operation
            pass
    """
    
    def __init__(self, max_concurrent: int = 5):
        """
        Initialize concurrency limiter.
        
        Args:
            max_concurrent: Maximum concurrent operations
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_count = 0
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        await self.semaphore.acquire()
        async with self._lock:
            self.active_count += 1
        return self
    
    async def __aexit__(self, *args):
        self.semaphore.release()
        async with self._lock:
            self.active_count -= 1
    
    @property
    def current_concurrency(self) -> int:
        """Get current number of active operations."""
        return self.active_count


class SessionManager:
    """
    Manage scraping session duration to avoid suspicion.
    
    Automatically tracks session time and can enforce maximum duration.
    """
    
    def __init__(self, max_duration_minutes: int = 30, warn_at_percent: int = 80):
        """
        Initialize session manager.
        
        Args:
            max_duration_minutes: Maximum session duration
            warn_at_percent: Warn when this percent of duration is reached
        """
        self.max_duration = timedelta(minutes=max_duration_minutes)
        self.warn_at_percent = warn_at_percent
        self.start_time: Optional[datetime] = None
        self.warned = False
    
    def start(self) -> None:
        """Start tracking session."""
        self.start_time = datetime.now()
        self.warned = False
    
    def elapsed(self) -> timedelta:
        """Get elapsed time."""
        if not self.start_time:
            return timedelta(0)
        return datetime.now() - self.start_time
    
    def remaining(self) -> timedelta:
        """Get remaining time."""
        return self.max_duration - self.elapsed()
    
    def should_continue(self) -> bool:
        """Check if session should continue."""
        return self.elapsed() < self.max_duration
    
    def should_warn(self) -> bool:
        """Check if warning threshold reached."""
        if self.warned:
            return False
        
        elapsed_percent = (self.elapsed() / self.max_duration) * 100
        if elapsed_percent >= self.warn_at_percent:
            self.warned = True
            return True
        return False
    
    def reset(self) -> None:
        """Reset session timer."""
        self.start_time = None
        self.warned = False


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter that adapts based on success/failure rates.
    
    Automatically slows down on errors, speeds up on success.
    """
    
    def __init__(self, initial_rate: int = 10, time_window: int = 60, **kwargs):
        super().__init__(initial_rate, time_window)
        self.initial_rate = initial_rate
        self.min_rate = max(1, initial_rate // 4)
        self.max_rate = initial_rate * 2
        self.error_count = 0
        self.success_count = 0
    
    def record_success(self) -> None:
        """Record successful request."""
        self.success_count += 1
        self.error_count = 0
        
        # Speed up gradually after consistent success
        if self.success_count >= 10 and self.max_requests < self.max_rate:
            self.max_requests = min(self.max_requests + 1, self.max_rate)
            self.success_count = 0
    
    def record_error(self) -> None:
        """Record failed request."""
        self.error_count += 1
        self.success_count = 0
        
        # Slow down immediately on errors
        if self.error_count >= 3:
            self.max_requests = max(self.max_requests // 2, self.min_rate)
            self.error_count = 0
    
    def reset_to_initial(self) -> None:
        """Reset to initial rate."""
        self.max_requests = self.initial_rate
        self.error_count = 0
        self.success_count = 0
        self.reset()
