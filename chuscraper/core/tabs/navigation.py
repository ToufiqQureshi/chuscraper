from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
from ... import cdp
from .base import TabMixin

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
        :param url: URL to navigate to.
        :param new_tab: Whether to open in a new tab.
        :param new_window: Whether to open in a new window.
        :param timeout: Time to wait for initial load (seconds)
        """
        if not self.browser:
            raise AttributeError("Tab has no browser, cannot use get()")

        if new_window or new_tab:
            return await self.browser.get(url, new_tab=new_tab, new_window=new_window)

        await self.send(cdp.page.navigate(url))
        try:
            # wait for idle state (production hardening)
            # using a shorter timeout for the initial get wait to prevent hangs
            # self.wait comes from WaitMixin
            await self.wait(timeout)
        except:
            pass
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
