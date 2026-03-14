from __future__ import annotations
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Optional
from ... import cdp
from .base import TabMixin

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from chuscraper.core.tab import Tab

class NavigationMixin(TabMixin):
    async def get(
        self,
        url: str = "about:blank",
        new_tab: bool = False,
        new_window: bool = False,
        timeout: int | float = 10,
    ) -> Tab:
        """
        Main navigation method.
        """
        if not self.browser:
            raise AttributeError("Tab has no browser, cannot use get()")

        if new_window or new_tab:
            return await self.browser.get(url, new_tab=new_tab, new_window=new_window)

        # Ensure DOM agent is active before navigation
        try: await self.send(cdp.dom.enable())
        except: pass

        await self.send(cdp.page.navigate(url))

        # Stability Fix: Handle about:blank race condition and wait for readyState transition
        loop = asyncio.get_running_loop()
        start_time = loop.time()

        # 1. Wait for URL to actually start changing or match target
        while loop.time() - start_time < timeout:
            try:
                current_url = await self.tab.evaluate("window.location.href")
                normalized_current = (current_url or "").lower().strip("/")
                normalized_target = url.lower().strip("/")

                # Check if we are at the target OR at least moved away from about:blank
                if normalized_target in ("about:blank", ""):
                    if normalized_current in ("about:blank", ""):
                         if self.tab.target: self.tab.target.url = "about:blank"
                         break
                elif normalized_current == normalized_target or (normalized_current != "about:blank" and normalized_current != ""):
                    if self.tab.target:
                            self.tab.target.url = current_url or url
                    break
            except Exception:
                pass
            await asyncio.sleep(0.2)

        # 2. Wait for readyState to move past 'loading'
        # Production Hardening: Check for modern single-page apps (SPAs)
        # that might stay in 'interactive' for a long time.
        while loop.time() - start_time < timeout:
            try:
                state = await self.tab.evaluate("document.readyState")
                if state in ("interactive", "complete"):
                    # For extra stability, check if body is present
                    has_body = await self.tab.evaluate("!!document.body")
                    if has_body:
                        break
            except Exception:
                pass
            await asyncio.sleep(0.5)

        # 3. Final small sleep to let layout settle
        await asyncio.sleep(0.3)

        return self.tab

    async def goto(self, url: str, **kwargs: Any) -> Tab:
        """Alias for get()."""
        return await self.get(url, **kwargs)

    async def back(self) -> None:
        """
        history back
        """
        await self.send(cdp.runtime.evaluate(expression="window.history.back()"))

    async def forward(self) -> None:
        """
        history forward
        """
        await self.send(cdp.runtime.evaluate(expression="window.history.forward()"))

    async def reload(
        self,
        ignore_cache: Optional[bool] = True,
        script_to_evaluate_on_load: Optional[str] = None,
    ) -> None:
        """
        Reloads the page

        :param ignore_cache: when set to True (default), it ignores cache, and re-downloads the items
        :param script_to_evaluate_on_load: script to run on load.
        """
        await self.send(
            cdp.page.reload(
                ignore_cache=ignore_cache,
                script_to_evaluate_on_load=script_to_evaluate_on_load,
            ),
        )

    async def title(self) -> str:
        """Returns the current page title."""
        return await self.evaluate("document.title")

    async def set_geolocation(self, latitude: float, longitude: float, accuracy: int = 100):
        """Sets the geolocation for the tab."""
        await self.send(cdp.emulation.set_geolocation_override(latitude, longitude, accuracy))
