from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING, Literal, Union

if TYPE_CHECKING:
    from ..tab import Tab
    from ..element import Element

class ActionsMixin(TabMixin):
    async def click(self, selector: str, mode: Literal["human", "fast", "cdp"] = "human", timeout: Optional[float] = None):
        """Finds and clicks an element."""
        el = await self.tab.select(selector, timeout=timeout)
        await el.click(mode=mode)
        return self.tab

    async def type(self, selector: str, text: str, delay: float = 0.05, timeout: Optional[float] = None):
        """Finds and types into an element with optional human-like delay."""
        el = await self.tab.select(selector, timeout=timeout)
        await el.type(text, delay=delay)
        return self.tab

    async def fill(self, selector: str, text: str, timeout: Optional[float] = None):
        """Finds, clears, and types into an element."""
        el = await self.tab.select(selector, timeout=timeout)
        await el.fill(text)
        return self.tab

    async def hover(self, selector: str, timeout: Optional[float] = None):
        """Finds and moves mouse to an element."""
        el = await self.tab.select(selector, timeout=timeout)
        await el.mouse_move()
        return self.tab

    async def send_keys(self, text: str):
        """Sends keys to the currently focused element."""
        from ..keys import KeyEvents, KeyPressEvent
        cluster_list = KeyEvents.from_text(text, KeyPressEvent.DOWN_AND_UP)
        for cluster in cluster_list:
             await self.send(self.cdp.input_.dispatch_key_event(**cluster))
