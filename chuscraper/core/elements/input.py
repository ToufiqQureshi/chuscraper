from __future__ import annotations
from .base import ElementMixin
from typing import TYPE_CHECKING, Literal, Optional, Union, List
import asyncio
import random
import logging
import typing
from ... import cdp
from .. import util
from ..keys import KeyEvents, KeyPressEvent, SpecialKeys

if TYPE_CHECKING:
    from ..element import Element

logger = logging.getLogger(__name__)

class ElementInputMixin(ElementMixin):
    async def click(
        self,
        mode: Literal["human", "fast", "cdp"] = "human",
        button: str = "left",
        click_count: int = 1,
        **kwargs
    ) -> None:
        if mode == "fast":
            if not self.remote_object:
                 setattr(self, '_remote_object', await self.tab.send(
                    cdp.dom.resolve_node(backend_node_id=self.backend_node_id)
                ))

            if self.remote_object.object_id is None:
                raise ValueError("could not resolve object id for %s" % self)

            arguments = [cdp.runtime.CallArgument(object_id=self.remote_object.object_id)]
            await self.flash(0.1)
            await self.tab.send(
                cdp.runtime.call_function_on(
                    "(el) => el.click()",
                    object_id=self.remote_object.object_id,
                    arguments=arguments,
                    await_promise=True,
                    user_gesture=True,
                    return_by_value=True,
                )
            )
            return

        # Scroll into view before clicking if using mouse events
        await self.scroll_into_view()
        pos = await self.get_position()
        if not pos:
            # Fallback to fast click if position unknown
            return await self.click(mode="fast")

        target_x, target_y = pos.center

        if mode == "human":
            from ..humanizer import Humanizer

            # Randomize destination slightly
            target_x += list(util.circle(0, 0, radius=3, num=1))[0][0]
            target_y += list(util.circle(0, 0, radius=3, num=1))[0][1]

            # Access hidden _last_mouse_x on tab? Tab implementation should expose these or we accept protected access
            last_x = getattr(self.tab, '_last_mouse_x', 0)
            last_y = getattr(self.tab, '_last_mouse_y', 0)

            path = Humanizer.bezier_curve(
                last_x, last_y,
                target_x, target_y,
                steps=Humanizer.get_mouse_steps(last_x, last_y, target_x, target_y)
            )

            for x, y in path:
                await self.tab.send(cdp.input_.dispatch_mouse_event(
                    type_="mouseMoved", x=x, y=y
                ))

            setattr(self.tab, '_last_mouse_x', target_x)
            setattr(self.tab, '_last_mouse_y', target_y)

            # Click
            await self.tab.send(cdp.input_.dispatch_mouse_event(
                type_="mousePressed", x=target_x, y=target_y, button=cdp.input_.MouseButton(button), click_count=click_count
            ))
            await asyncio.sleep(random.uniform(0.05, 0.15)) # Key down delay
            await self.tab.send(cdp.input_.dispatch_mouse_event(
                type_="mouseReleased", x=target_x, y=target_y, button=cdp.input_.MouseButton(button), click_count=click_count
            ))

        elif mode == "cdp":
            await self.tab.send(cdp.input_.dispatch_mouse_event(
                type_="mousePressed", x=target_x, y=target_y, button=cdp.input_.MouseButton(button), click_count=click_count
            ))
            await self.tab.send(cdp.input_.dispatch_mouse_event(
                type_="mouseReleased", x=target_x, y=target_y, button=cdp.input_.MouseButton(button), click_count=click_count
            ))

    async def fill(self, text: str) -> None:
        await self.click(mode="human") # Focus
        await self.clear_input()
        await self.send_keys(text)

    async def type(self, text: str, delay: float = 0.0) -> None:
        """Alias for send_keys with optional delay per char."""
        if delay > 0:
            for char in text:
                await self.send_keys(char)
                await asyncio.sleep(delay)
        else:
            await self.send_keys(text)

    async def send_keys(
        self, text: typing.Union[str, SpecialKeys, typing.List[KeyEvents.Payload]]
    ) -> None:
        await self.apply("(elem) => elem.focus()")
        cluster_list: typing.List[KeyEvents.Payload]
        if isinstance(text, str):
            cluster_list = KeyEvents.from_text(text, KeyPressEvent.CHAR)
        elif isinstance(text, SpecialKeys):
            cluster_list = KeyEvents(text).to_cdp_events(KeyPressEvent.DOWN_AND_UP)
        else:
            cluster_list = text

        for cluster in cluster_list:
            await self.tab.send(cdp.input_.dispatch_key_event(**cluster))

    async def mouse_click(
        self,
        button: str = "left",
        buttons: typing.Optional[int] = 1,
        modifiers: typing.Optional[int] = 0,
        hold: bool = False,
        _until_event: typing.Optional[type] = None,
    ) -> None:
        position = await self.get_position()
        if not position:
            logger.warning("could not find location for %s, not clicking", self)
            return
        center = position.center
        logger.debug("clicking on location %.2f, %.2f" % center)

        await asyncio.gather(
            self.tab.send(
                cdp.input_.dispatch_mouse_event(
                    "mousePressed",
                    x=center[0],
                    y=center[1],
                    modifiers=modifiers,
                    button=cdp.input_.MouseButton(button),
                    buttons=buttons,
                    click_count=1,
                )
            ),
            self.tab.send(
                cdp.input_.dispatch_mouse_event(
                    "mouseReleased",
                    x=center[0],
                    y=center[1],
                    modifiers=modifiers,
                    button=cdp.input_.MouseButton(button),
                    buttons=buttons,
                    click_count=1,
                )
            ),
        )
        try:
            await self.flash()
        except:  # noqa
            pass

    async def mouse_move(self) -> None:
        position = await self.get_position()
        if not position:
            logger.warning("could not find location for %s, not moving mouse", self)
            return
        center = position.center
        await self.tab.send(
            cdp.input_.dispatch_mouse_event("mouseMoved", x=center[0], y=center[1])
        )
        await self.tab.sleep(0.05)
        await self.tab.send(
            cdp.input_.dispatch_mouse_event("mouseReleased", x=center[0], y=center[1])
        )

    async def mouse_drag(
        self,
        destination: typing.Union[Element, typing.Tuple[int, int]],
        relative: bool = False,
        steps: int = 1,
    ) -> None:
        # Avoid circular import by importing Element only for type check if needed or assuming strict typing
        # Here we use 'Element' from TYPE_CHECKING which is fine.
        start_position = await self.get_position()
        if not start_position:
            logger.warning("could not find location for %s, not dragging", self)
            return
        start_point = start_position.center
        end_point = None

        # Check type at runtime without importing Element if possible, or use string check/duck typing
        if hasattr(destination, 'get_position'):
            end_position = await destination.get_position()
            if not end_position:
                return
            end_point = end_position.center
        elif isinstance(destination, (tuple, list)):
            if relative:
                end_point = (
                    start_point[0] + destination[0],
                    start_point[1] + destination[1],
                )
            else:
                end_point = destination

        from ..humanizer import Humanizer

        await self.tab.send(
            cdp.input_.dispatch_mouse_event(
                "mousePressed",
                x=start_point[0],
                y=start_point[1],
                button=cdp.input_.MouseButton("left"),
            )
        )

        steps = steps or Humanizer.get_mouse_steps(start_point[0], start_point[1], end_point[0], end_point[1])
        path = Humanizer.bezier_curve(
            start_point[0], start_point[1],
            end_point[0], end_point[1],
            steps=steps
        )

        for x, y in path:
            await self.tab.send(
                cdp.input_.dispatch_mouse_event(
                    "mouseMoved",
                    x=x,
                    y=y,
                )
            )
            if random.random() > 0.9:
                await asyncio.sleep(random.uniform(0.001, 0.005))

        await self.tab.send(
            cdp.input_.dispatch_mouse_event(
                type_="mouseReleased",
                x=end_point[0],
                y=end_point[1],
                button=cdp.input_.MouseButton("left"),
            )
        )
