from __future__ import annotations
import asyncio
from .base import TabMixin
from typing import TYPE_CHECKING, Literal, Optional, Union
import typing
import secrets
import logging
from ... import cdp

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..tab import Tab
    from ..element import Element

class ActionsMixin(TabMixin):
    async def _retry_action(self, func, selector, *args, timeout=None, **kwargs):
        """Internal helper to implement retry_enabled switch."""
        config = self.tab.browser.config if self.tab.browser else None
        retry_enabled = getattr(config, "retry_enabled", False)
        retry_count = getattr(config, "retry_count", 3) if retry_enabled else 1
        retry_timeout = getattr(config, "retry_timeout", 10.0)

        last_exc = None
        for i in range(retry_count):
            try:
                el = await self.tab.select(selector, timeout=timeout)
                return await func(el, *args, **kwargs)
            except Exception as e:
                last_exc = e
                if not retry_enabled:
                    break
                logger.debug(f"Retrying action on {selector} ({i+1}/{retry_count}) after error: {e}")
                await asyncio.sleep(retry_timeout / retry_count)

        raise last_exc

    async def click(self, selector: str, mode: Literal["human", "fast", "cdp"] = "human", timeout: Optional[float] = None):
        """Finds and clicks an element."""
        await self._retry_action(lambda el: el.click(mode=mode), selector, timeout=timeout)
        return self.tab

    async def type(self, selector: str, text: str, delay: float = 0.05, timeout: Optional[float] = None):
        """Finds and types into an element with optional human-like delay."""
        await self._retry_action(lambda el: el.send_keys(text), selector, timeout=timeout)
        return self.tab

    async def fill(self, selector: str, text: str, timeout: Optional[float] = None):
        """Finds, clears, and types into an element."""
        await self._retry_action(lambda el: el.fill(text), selector, timeout=timeout)
        return self.tab

    async def human_click(self, selector: str, timeout: Optional[float] = None):
        """Alias for click(mode='human')."""
        return await self.click(selector, mode="human", timeout=timeout)

    async def human_type(self, selector: str, text: str, delay: float = 0.1, timeout: Optional[float] = None):
        """Alias for type() with a slightly longer default human delay."""
        return await self.type(selector, text, delay=delay, timeout=timeout)

    async def human_fill(self, selector: str, text: str, timeout: Optional[float] = None):
        """Finds element, clicks it humanly, and fills it."""
        el = await self.tab.select(selector, timeout=timeout)
        await el.click(mode="human")
        await el.fill(text)
        return self.tab

    async def submit(self, selector: str = "form", timeout: Optional[float] = None):
        """Finds a form or submit button and triggers submission."""
        el = await self.tab.select(selector, timeout=timeout)
        if el.node_name == "FORM":
            await el.apply("(form) => form.submit()")
        else:
            # Assume it's a button, use human click
            await el.click(mode="human")
        return self.tab

    async def hover(self, selector: str, timeout: Optional[float] = None):
        """Finds and moves mouse to an element."""
        el = await self.tab.select(selector, timeout=timeout)
        if el:
            await el.mouse_move() # explicitly call interaction method
        return self.tab

    async def send_keys(self, text: str):
        """Sends keys to the currently focused element."""
        from ..keys import KeyEvents, KeyPressEvent
        cluster_list = KeyEvents.from_text(text, KeyPressEvent.DOWN_AND_UP)
        for cluster in cluster_list:
             await self.send(self.cdp.input_.dispatch_key_event(**cluster))

    async def mouse_move(
        self, x: float, y: float, steps: int = 10, flash: bool = False
    ) -> None:
        steps = 1 if (not steps or steps < 1) else steps
        # probably the worst waay of calculating this. but couldn't think of a better solution today.
        if steps > 1:
            step_size_x = x // steps
            step_size_y = y // steps
            pathway = [(step_size_x * i, step_size_y * i) for i in range(steps + 1)]
            for point in pathway:
                if flash:
                    await self.flash_point(point[0], point[1])
                await self.send(
                    cdp.input_.dispatch_mouse_event(
                        "mouseMoved", x=point[0], y=point[1]
                    )
                )
        else:
            await self.send(cdp.input_.dispatch_mouse_event("mouseMoved", x=x, y=y))
        if flash:
            await self.flash_point(x, y)
        else:
            await self.tab.sleep(0.05)
        await self.send(cdp.input_.dispatch_mouse_event("mouseReleased", x=x, y=y))
        if flash:
            await self.flash_point(x, y)

    async def mouse_click(
        self,
        x: float,
        y: float,
        button: str = "left",
        buttons: typing.Optional[int] = 1,
        modifiers: typing.Optional[int] = 0,
        _until_event: typing.Optional[type] = None,
        flash: typing.Optional[bool] = False,
    ) -> None:
        """native click on position x,y
        :param y:
        :param x:
        :param button: str (default = "left")
        :param buttons: which button (default 1 = left)
        :param modifiers: *(Optional)* Bit field representing pressed modifier keys.
                Alt=1, Ctrl=2, Meta/Command=4, Shift=8 (default: 0).
        :param _until_event: internal. event to wait for before returning
        :return:
        """

        await self.send(
            cdp.input_.dispatch_mouse_event(
                "mousePressed",
                x=x,
                y=y,
                modifiers=modifiers,
                button=cdp.input_.MouseButton(button),
                buttons=buttons,
                click_count=1,
            )
        )

        await self.send(
            cdp.input_.dispatch_mouse_event(
                "mouseReleased",
                x=x,
                y=y,
                modifiers=modifiers,
                button=cdp.input_.MouseButton(button),
                buttons=buttons,
                click_count=1,
            )
        )
        if flash:
            await self.flash_point(x, y)

    async def flash_point(
        self, x: float, y: float, duration: float = 0.5, size: int = 10
    ) -> None:
        style = (
            "position:fixed;z-index:99999999;padding:0;margin:0;"
            "left:{:.1f}px; top: {:.1f}px;"
            "opacity:1;"
            "width:{:d}px;height:{:d}px;border-radius:50%;background:red;"
            "animation:show-pointer-ani {:.2f}s ease 1;"
        ).format(x - 8, y - 8, size, size, duration)
        script = (
            """
                var css = document.styleSheets[0];
                for( let css of [...document.styleSheets]) {{
                    try {{
                        css.insertRule(`
                        @keyframes show-pointer-ani {{
                              0% {{ opacity: 1; transform: scale(1, 1);}}
                              50% {{ transform: scale(3, 3);}}
                              100% {{ transform: scale(1, 1); opacity: 0;}}
                        }}`,css.cssRules.length);
                        break;
                    }} catch (e) {{
                        console.log(e)
                    }}
                }};
                var _d = document.createElement('div');
                _d.style = `{0:s}`;
                _d.id = `{1:s}`;
                document.body.insertAdjacentElement('afterBegin', _d);

                setTimeout( () => document.getElementById('{1:s}').remove(), {2:d});

            """.format(style, secrets.token_hex(8), int(duration * 1000))
            .replace("  ", "")
            .replace("\n", "")
        )
        await self.send(
            cdp.runtime.evaluate(
                script,
                await_promise=True,
                user_gesture=True,
            )
        )
