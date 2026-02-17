from __future__ import annotations
from .base import TabMixin
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..tab import Tab

class WaitMixin(TabMixin):
    async def wait_for_selector(self, selector: str, timeout: float = 10.0):
        """Wait for an element to appear in DOM."""
        return await self.tab.select(selector, timeout=timeout)

    async def wait_for_idle(self, timeout: float = 15.0):
        """Wait for network and lifecycle idle."""
        await self.tab.wait(timeout)

    async def sleep(self, seconds: float):
        """Async sleep."""
        await asyncio.sleep(seconds)
