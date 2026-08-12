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

    async def wait_for_idle(self, timeout: float = 15.0, idle_time: float = 0.5) -> bool:
        """
        Wait until the document has finished loading and the network goes quiet.

        Polls ``document.readyState`` plus the count of in-flight fetch/XHR
        requests, and returns as soon as the page has been quiet for
        `idle_time` seconds - rather than always burning the full timeout.

        :param timeout: give up after this many seconds
        :param idle_time: how long the page must stay quiet to count as idle
        :return: True if the page went idle, False if we hit the timeout
        """
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        quiet_since: Optional[float] = None

        # Count in-flight requests by patching fetch/XHR once per document.
        probe = """
        (() => {
          if (!window.__chu_inflight_installed) {
            window.__chu_inflight = 0;
            window.__chu_inflight_installed = true;
            const of = window.fetch;
            if (of) {
              window.fetch = function(...a) {
                window.__chu_inflight++;
                return of.apply(this, a).finally(() => { window.__chu_inflight--; });
              };
            }
            const os = XMLHttpRequest.prototype.send;
            XMLHttpRequest.prototype.send = function(...a) {
              window.__chu_inflight++;
              this.addEventListener('loadend', () => { window.__chu_inflight--; });
              return os.apply(this, a);
            };
          }
          return document.readyState + '|' + (window.__chu_inflight || 0);
        })()
        """

        while loop.time() < deadline:
            try:
                state = await self.tab.evaluate(probe)
            except Exception:
                state = None

            is_idle = False
            if isinstance(state, str) and "|" in state:
                ready, _, inflight = state.partition("|")
                is_idle = ready == "complete" and inflight.strip() in ("0", "")

            if is_idle:
                if quiet_since is None:
                    quiet_since = loop.time()
                elif loop.time() - quiet_since >= idle_time:
                    return True
            else:
                quiet_since = None

            await asyncio.sleep(0.1)

        return False
