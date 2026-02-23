from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING, Optional
import base64

if TYPE_CHECKING:
    from ..tab import Tab

class ScreenshotMixin(TabMixin):
    async def save_screenshot(self, filename: str, full_page: bool = False):
        """Saves a screenshot to file."""
        data = await self.tab.screenshot(full_page=full_page)
        with open(filename, "wb") as f:
            f.write(data)

    async def screenshot(self, full_page: bool = False) -> bytes:
        """Returns screenshot as bytes."""
        if full_page:
            # CDP Page.get_layout_metrics for full page
            metrics = await self.send(self.cdp.page.get_layout_metrics())
            # index 5 is cssContentSize which is more reliable for screenshots
            content_size = metrics[5] 
            width = content_size.width
            height = content_size.height
            await self.send(self.cdp.emulation.set_device_metrics_override(
                width=int(width), height=int(height), 
                device_scale_factor=1, mobile=False
            ))
            
        res = await self.send(self.cdp.page.capture_screenshot(format_="png"))
        if not res:
             from ..connection import ProtocolException
             raise ProtocolException("could not take screenshot")
        return base64.b64decode(res)
