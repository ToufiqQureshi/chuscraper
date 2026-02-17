from __future__ import annotations
import asyncio
import logging
import functools
from typing import TYPE_CHECKING, Any, Callable, TypeVar, Optional

if TYPE_CHECKING:
    from ..tab import Tab
    from ..connection import Connection

logger = logging.getLogger(__name__)
T = TypeVar("T")

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: bool = True):
    """Decorator for production-safe retries with exponential backoff."""
    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any):
            last_err = None
            for attempt in range(max_attempts):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    last_err = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (2 ** attempt if backoff else 1)
                        logger.warning(f"Attempt {attempt+1} failed for {func.__name__}: {e}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
            raise last_err
        return wrapper
    return decorator

class TabMixin:
    """Base class for Tab components."""
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__() # Terminate or pass up the chain

    @property
    def tab(self) -> Any:
        return self

    @property
    def send(self) -> Any:
        # Connection provides send()
        return getattr(self, "send_command", getattr(self, "send", None))

    @property
    def timeout(self) -> float:
        return getattr(self.tab, "_timeout", 30.0)
