from __future__ import annotations
from .base import TabMixin
import asyncio
from typing import TYPE_CHECKING, Union, Optional, Literal

if TYPE_CHECKING:
    from ..tab import Tab
    from ..element import Element

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

    async def wait_for(
        self,
        selector: str | None = None,
        text: str | None = None,
        timeout: int | float = 10,
    ) -> Element:
        """
        variant on query_selector_all and find_elements_by_text
        this variant takes either selector or text, and will block until
        the requested element(s) are found.

        it will block for a maximum of <timeout> seconds, after which
        a TimeoutError will be raised

        :param selector: css selector
        :param text: text
        :param timeout:
        :return:
        :rtype: Element
        :raises asyncio.TimeoutError:
        """
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        if selector:
            item = await self.tab.query_selector(selector)
            while not item and loop.time() - start_time < timeout:
                item = await self.tab.query_selector(selector)
                await self.sleep(0.5)

            if item:
                return item
        if text:
            item = await self.tab.find_element_by_text(text)
            while not item and loop.time() - start_time < timeout:
                item = await self.tab.find_element_by_text(text)
                await self.sleep(0.5)

            if item:
                return item

        raise asyncio.TimeoutError("time ran out while waiting")

    async def wait_for_ready_state(
        self,
        until: Literal["loading", "interactive", "complete"] = "interactive",
        timeout: int = 10,
    ) -> bool:
        """
        Waits for the page to reach a certain ready state.
        :param until: The ready state to wait for. Can be one of "loading", "interactive", or "complete".
        :param timeout: The maximum number of seconds to wait.
        :raises asyncio.TimeoutError: If the timeout is reached before the ready state is reached.
        :return: True if the ready state is reached.
        :rtype: bool
        """
        loop = asyncio.get_event_loop()
        start_time = loop.time()

        while True:
            ready_state = await self.tab.evaluate("document.readyState")
            if ready_state == until:
                return True

            if loop.time() - start_time > timeout:
                raise asyncio.TimeoutError(
                    "time ran out while waiting for load page until %s" % until
                )

            await asyncio.sleep(0.1)
