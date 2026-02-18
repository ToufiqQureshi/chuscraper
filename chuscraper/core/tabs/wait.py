from __future__ import annotations
from .base import TabMixin
import asyncio
from typing import TYPE_CHECKING, Union, Optional

if TYPE_CHECKING:
    from ..tab import Tab

class WaitMixin(TabMixin):
    async def wait(self, time: Union[float, int] = 1) -> Tab:
        """
        Wait for <time> seconds.
        :param time:
        :return: self
        """
        await asyncio.sleep(time)
        return self.tab

    async def sleep(self, seconds: float = 1.0) -> None:
        """Utility method to let the script 'breathe'."""
        await asyncio.sleep(seconds)

    async def wait_for_selector(self, selector: str, timeout: float = 10.0):
        """Wait for an element to appear in DOM."""
        return await self.tab.select(selector, timeout=timeout)

    async def wait_for_idle(self, timeout: float = 15.0):
        """Wait for network and lifecycle idle."""
        await self.tab.wait(timeout)
