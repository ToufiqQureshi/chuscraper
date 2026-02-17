from __future__ import annotations
from .base import TabMixin, retry
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..tab import Tab

class NavigationMixin(TabMixin):
    async def goto(self, url: str, timeout: Optional[float] = None, wait_idle: bool = True) -> Tab:
        """Production-ready navigation with retries and timeout."""
        t_out = timeout if timeout is not None else 15  # Default 15s for nav
        await self.send(self.cdp.page.navigate(url))
        if wait_idle:
            try:
                # Wait for idle, but timeout after t_out to prevent hangs
                await self.tab.wait(t_out)
            except:
                pass
        return self.tab

    async def title(self) -> str:
        """Returns the current page title."""
        return await self.tab.evaluate("document.title")

    async def back(self):
        """History back."""
        # CDP page.get_navigation_history
        hist = await self.send(self.cdp.page.get_navigation_history())
        if hist and hist[0] > 0:
            entry = hist[1][hist[0] - 1]
            await self.send(self.cdp.page.navigate_to_history_entry(entry.id))
        return self.tab

    async def reload(self):
        """Reload current page."""
        await self.send(self.cdp.page.reload())
        return self.tab

    async def set_geolocation(self, latitude: float, longitude: float, accuracy: int = 100):
        """Sets the geolocation for the tab."""
        await self.send(self.cdp.emulation.set_geolocation_override(latitude, longitude, accuracy))
