from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING
import base64


class ScreenshotMixin(TabMixin):
    async def save_screenshot(self, filename: str, full_page: bool = False):
        """Saves a screenshot to file."""
        data = await self.tab.screenshot(full_page=full_page)
        with open(filename, "wb") as f:
            f.write(data)

    async def screenshot(self, full_page: bool = False) -> bytes:
        """Returns screenshot as bytes."""
        resized = False
        try:
            if full_page:
                # Page.getLayoutMetrics returns (layoutViewport, visualViewport,
                # contentSize, cssLayoutViewport, cssVisualViewport, cssContentSize).
                # cssContentSize is the reliable one for screenshots.
                metrics = await self.send(self.cdp.page.get_layout_metrics())
                content_size = metrics[5] if len(metrics) > 5 else metrics[2]
                width = int(content_size.width)
                height = int(content_size.height)
                await self.send(self.cdp.emulation.set_device_metrics_override(
                    width=width, height=height,
                    device_scale_factor=1, mobile=False
                ))
                resized = True

            res = await self.send(self.cdp.page.capture_screenshot(format_="png"))
            if not res:
                from ..connection import ProtocolException
                raise ProtocolException("could not take screenshot")
            return base64.b64decode(res)
        finally:
            if resized:
                # Always hand the viewport back. Leaving the override in place
                # left every later interaction (and any stealth viewport we had
                # applied) stuck at full-page height for the rest of the session.
                try:
                    await self._restore_viewport()
                except Exception:
                    pass

    async def _restore_viewport(self) -> None:
        """Undo a temporary device-metrics override, re-applying stealth if set."""
        profile = getattr(getattr(self.tab, "browser", None), "_stealth_profile", None)
        if profile is not None:
            # Restore the *viewport*, not the screen size - stealth deliberately
            # keeps the viewport smaller than the screen.
            await self.send(self.cdp.emulation.set_device_metrics_override(
                width=profile.viewport_width, height=profile.viewport_height,
                device_scale_factor=1, mobile=False,
            ))
        else:
            await self.send(self.cdp.emulation.clear_device_metrics_override())
