from __future__ import annotations
from .base import TabMixin
from ... import cdp
from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..tab import Tab

class WindowMixin(TabMixin):
    async def get_window(self) -> Tuple[cdp.browser.WindowID, cdp.browser.Bounds]:
        """
        get the window Bounds
        :return:
        :rtype:
        """
        window_id, bounds = await self.send(
            cdp.browser.get_window_for_target(self.tab.target_id)
        )
        return window_id, bounds

    async def maximize(self) -> None:
        """
        maximize page/tab/window
        """
        return await self.set_window_state(state="maximize")

    async def minimize(self) -> None:
        """
        minimize page/tab/window
        """
        return await self.set_window_state(state="minimize")

    async def fullscreen(self) -> None:
        """
        minimize page/tab/window
        """
        return await self.set_window_state(state="fullscreen")

    async def medimize(self) -> None:
        return await self.set_window_state(state="normal")

    async def set_window_size(
        self, left: int = 0, top: int = 0, width: int = 1280, height: int = 1024
    ) -> None:
        """
        set window size and position

        :param left: pixels from the left of the screen to the window top-left corner
        :param top: pixels from the top of the screen to the window top-left corner
        :param width: width of the window in pixels
        :param height: height of the window in pixels
        :return:
        :rtype:
        """
        return await self.set_window_state(left, top, width, height)

    async def activate(self) -> None:
        """
        active this target (ie: tab,window,page)
        """
        if self.tab.target is None:
            raise ValueError("target is none")
        await self.send(cdp.target.activate_target(self.tab.target.target_id))

    async def bring_to_front(self) -> None:
        """
        alias to self.activate
        """
        await self.activate()

    async def set_window_state(
        self,
        left: int = 0,
        top: int = 0,
        width: int = 1280,
        height: int = 720,
        state: str = "normal",
    ) -> None:
        """
        sets the window size or state.

        for state you can provide the full name like minimized, maximized, normal, fullscreen, or
        something which leads to either of those, like min, mini, mi,  max, ma, maxi, full, fu, no, nor
        in case state is set other than "normal", the left, top, width, and height are ignored.

        :param left: desired offset from left, in pixels
        :param top: desired offset from the top, in pixels
        :param width: desired width in pixels
        :param height: desired height in pixels
        :param state:
            can be one of the following strings:
                - normal
                - fullscreen
                - maximized
                - minimized
        """
        available_states = ["minimized", "maximized", "fullscreen", "normal"]
        window_id: cdp.browser.WindowID
        bounds: cdp.browser.Bounds
        (window_id, bounds) = await self.get_window()

        for state_name in available_states:
            if all(x in state_name for x in state.lower()):
                break
        else:
            raise NameError(
                "could not determine any of %s from input '%s'"
                % (",".join(available_states), state)
            )
        window_state = getattr(
            cdp.browser.WindowState, state_name.upper(), cdp.browser.WindowState.NORMAL
        )
        if window_state == cdp.browser.WindowState.NORMAL:
            bounds = cdp.browser.Bounds(left, top, width, height, window_state)
        else:
            # min, max, full can only be used when current state == NORMAL
            # therefore we first switch to NORMAL
            await self.set_window_state(state="normal")
            bounds = cdp.browser.Bounds(window_state=window_state)

        await self.send(cdp.browser.set_window_bounds(window_id, bounds=bounds))
