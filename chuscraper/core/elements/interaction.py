from __future__ import annotations
from .base import ElementMixin
from typing import TYPE_CHECKING, Literal, Any, Optional, Union, Tuple
import asyncio
import json
import logging
import typing
import random
import math

from ... import cdp
from .. import util
from ..config import PathLike
from ..keys import KeyEvents, KeyPressEvent, SpecialKeys

if TYPE_CHECKING:
    from ..element import Element
    from .._contradict import ContraDict

logger = logging.getLogger(__name__)

def cubic_bezier(t: float, p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> tuple[float, float]:
    """Calculate point on a cubic bezier curve at time t (0.0 to 1.0)"""
    x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
    y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
    return (x, y)

class Position(cdp.dom.Quad):
    """helper class for element positioning"""

    def __init__(self, points: list[float]):
        super().__init__(points)
        (
            self.left,
            self.top,
            self.right,
            self.top,
            self.right,
            self.bottom,
            self.left,
            self.bottom,
        ) = points
        self.abs_x: float = 0
        self.abs_y: float = 0
        self.x = self.left
        self.y = self.top
        self.height, self.width = (self.bottom - self.top, self.right - self.left)
        self.center = (
            self.left + (self.width / 2),
            self.top + (self.height / 2),
        )

    def to_viewport(self, scale: float = 1) -> cdp.page.Viewport:
        return cdp.page.Viewport(
            x=self.x, y=self.y, width=self.width, height=self.height, scale=scale
        )

    def __repr__(self) -> str:
        return f"<Position(x={self.left}, y={self.top}, width={self.width}, height={self.height})>"

class ElementInteractionMixin(ElementMixin):
    """Mixin for Element interactions."""
    
    _remote_object: cdp.runtime.RemoteObject | None

    @property
    def object_id(self) -> cdp.runtime.RemoteObjectId | None:
        if not hasattr(self, 'remote_object') or not self.remote_object:
            return None
        return self.remote_object.object_id
    
    @property
    def remote_object(self) -> cdp.runtime.RemoteObject | None:
        return self._remote_object

    async def update(self, _node: cdp.dom.Node | None = None) -> Element:
        if _node:
            doc = _node
        else:
            doc = await self.tab.send(cdp.dom.get_document(-1, True))
        
        current_node = getattr(self, '_node')
        updated_node = util.filter_recurse(
            doc, lambda n: n.backend_node_id == current_node.backend_node_id
        )
        if updated_node:
            logger.debug("node seems changed, and has now been updated.")
            setattr(self, '_node', updated_node)
        
        setattr(self, '_tree', doc)

        new_remote_obj = await self.tab.send(
            cdp.dom.resolve_node(backend_node_id=getattr(self, '_node').backend_node_id)
        )
        setattr(self, '_remote_object', new_remote_obj)
        
        self.attrs.clear()
        if hasattr(self, '_make_attrs'):
            self._make_attrs() # type: ignore
            
        return self # type: ignore

    async def save_to_dom(self) -> None:
        ro = await self.tab.send(
            cdp.dom.resolve_node(backend_node_id=self.backend_node_id)
        )
        setattr(self, '_remote_object', ro)
        await self.tab.send(cdp.dom.set_outer_html(self.node_id, outer_html=str(self)))
        await self.update()

    async def remove_from_dom(self) -> None:
        await self.update()
        if not self.tree:
            raise RuntimeError(
                "could not remove from dom since the element has no tree set"
            )
        node = util.filter_recurse(
            self.tree, lambda node: node.backend_node_id == self.backend_node_id
        )
        if node:
            await self.tab.send(cdp.dom.remove_node(node.node_id))

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
            # Add small random offset to target to avoid clicking exact center every time
            # Assuming elements are usually larger than 1x1, limit offset to stay inside
            offset_x = random.uniform(-pos.width/4, pos.width/4)
            offset_y = random.uniform(-pos.height/4, pos.height/4)
            target_x += offset_x
            target_y += offset_y

            # Retrieve last mouse position from Tab state
            last_x = getattr(self.tab, '_last_mouse_x', 0)
            last_y = getattr(self.tab, '_last_mouse_y', 0)
            
            # Distance check
            dist = math.hypot(target_x - last_x, target_y - last_y)

            # Bezier Control Points
            if dist > 10:
                # Perpendicular vector for randomness
                ux = (target_x - last_x) / dist
                uy = (target_y - last_y) / dist
                px = -uy
                py = ux

                # Deviation amount scales with distance
                deviation = min(dist/3, 150) * random.uniform(-1, 1)

                p1 = (last_x + (target_x - last_x)/3 + px * deviation,
                      last_y + (target_y - last_y)/3 + py * deviation)
                p2 = (last_x + 2*(target_x - last_x)/3 + px * deviation,
                      last_y + 2*(target_y - last_y)/3 + py * deviation)
            else:
                p1 = (last_x, last_y)
                p2 = (target_x, target_y)

            # More steps for longer distances, min 25 steps for smoothness
            steps = max(25, int(dist / 7))

            for i in range(1, steps + 1):
                t = i / steps
                # Ease-in-out function for realistic acceleration/deceleration
                # smoothstep: t * t * (3 - 2 * t)
                t_eased = t * t * (3 - 2 * t)

                mx, my = cubic_bezier(t_eased, (last_x, last_y), p1, p2, (target_x, target_y))

                await self.tab.send(cdp.input_.dispatch_mouse_event(
                    type_="mouseMoved", x=mx, y=my
                ))

                # Update last mouse position on tab
                self.tab._last_mouse_x = mx
                self.tab._last_mouse_y = my

                # Micro-sleeps every few steps to simulate processing/friction
                if i % random.randint(3, 7) == 0:
                    await asyncio.sleep(random.uniform(0.0005, 0.002))
            
            # Click with human duration
            await self.tab.send(cdp.input_.dispatch_mouse_event(
                type_="mousePressed", x=target_x, y=target_y, button=cdp.input_.MouseButton(button), click_count=click_count
            ))

            # Human click hold duration: 60ms to 150ms
            await asyncio.sleep(random.uniform(0.06, 0.15))

            await self.tab.send(cdp.input_.dispatch_mouse_event(
                type_="mouseReleased", x=target_x, y=target_y, button=cdp.input_.MouseButton(button), click_count=click_count
            ))

        else:
            # Fallback for "cdp" mode (instant but using mouse events)
            await self.tab.send(cdp.input_.dispatch_mouse_event(
                type_="mouseMoved", x=target_x, y=target_y
            ))
            await self.tab.send(cdp.input_.dispatch_mouse_event(
                type_="mousePressed", x=target_x, y=target_y, button=cdp.input_.MouseButton(button), click_count=click_count
            ))
            await self.tab.send(cdp.input_.dispatch_mouse_event(
                type_="mouseReleased", x=target_x, y=target_y, button=cdp.input_.MouseButton(button), click_count=click_count
            ))

    async def fill(self, text: str) -> None:
        await self.click(mode="human")  # Use human click to focus
        await self.clear_input()
        await self.type(text) # Calls upgraded type method

    async def type(self, text: str, delay: float = 0.0) -> None:
        """Human-like typing with variable delays and mistakes"""
        # Initial "thinking" pause before typing starts
        await asyncio.sleep(random.uniform(0.1, 0.4))

        for char in text:
            # 3% chance of mistake if text length > 5
            if len(text) > 5 and random.random() < 0.03:
                # Type a random wrong character
                wrong_char = chr(ord(char) + random.choice([-1, 1]))
                await self.send_keys(wrong_char)
                await asyncio.sleep(random.uniform(0.1, 0.25))
                # Backspace
                await self.send_keys(SpecialKeys.BACKSPACE)
                await asyncio.sleep(random.uniform(0.1, 0.2))
            
            await self.send_keys(char)

            # Human typing rhythm: average ~100-150ms between keys, normal distribution
            # Fast typist: 60-100ms, Slow: 150-250ms. Let's aim for "Average Internet User" ~120ms
            base_delay = 0.12
            variation = 0.04

            d = random.gauss(base_delay, variation)
            d = max(0.03, min(d, 0.35)) # Clamp to realistic bounds

            await asyncio.sleep(d + delay)

    async def send_keys(
        self, text: typing.Union[str, SpecialKeys, typing.List[KeyEvents.Payload]]
    ) -> None:
        # We don't force focus() here every time because it breaks the flow if called repeatedly in type()
        # Instead, we assume focus is set by click() or caller.
        # But for robustness, we can check if focused? No, CDP doesn't easily tell us.
        # The old code called focus() every time. Let's keep it but maybe optimize?
        # Actually, focus() every char might be weird/slow.
        # But removing it might break tests if they rely on send_keys focusing.
        # Let's keep it but make it check if we just clicked it.
        # For now, safe to leave as is, just overhead.

        # NOTE: Keeping focus() call for safety
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

    async def clear_input(self) -> None:
        """clears an input field"""
        await self.apply('function (element) { element.value = "" } ')

    async def clear_input_by_deleting(self) -> None:
        await self.apply(
            """
                async function clearByDeleting(n, d = 50) {
                    n.focus();
                    n.setSelectionRange(0, 0);
                    while (n.value.length > 0) {
                        n.dispatchEvent(
                            new KeyboardEvent("keydown", {
                                key: "Delete",
                                code: "Delete",
                                keyCode: 46,
                                which: 46,
                                bubbles: !0,
                                cancelable: !0,
                            })
                        );
                        n.dispatchEvent(
                            new KeyboardEvent("keypress", {
                                key: "Delete",
                                code: "Delete",
                                keyCode: 46,
                                which: 46,
                                bubbles: !0,
                                cancelable: !0,
                            })
                        );
                         n.dispatchEvent(
                            new InputEvent("beforeinput", {
                                inputType: "deleteContentForward",
                                data: null,
                                bubbles: !0,
                                cancelable: !0,
                            })
                        );
                        n.dispatchEvent(
                            new KeyboardEvent("keyup", {
                                key: "Delete",
                                code: "Delete",
                                keyCode: 46,
                                which: 46,
                                bubbles: !0,
                                cancelable: !0,
                            })
                        );
                        n.value = n.value.slice(1);
                        await new Promise((r) => setTimeout(r, d));
                    }
                    n.dispatchEvent(new Event("input", { bubbles: !0 }));
                }
            """,
            await_promise=True,
        )

    async def send_file(self, *file_paths: PathLike) -> None:
        file_paths_as_str = [str(p) for p in file_paths]
        await self.tab.send(
            cdp.dom.set_file_input_files(
                files=[*file_paths_as_str],
                backend_node_id=self.backend_node_id,
                object_id=self.object_id,
            )
        )

    async def focus(self) -> None:
        await self.apply("(element) => element.focus()")

    async def select_option(self) -> None:
        if self.node_name == "OPTION":
            await self.apply(
                """
                (o) => {
                    o.selected = true ;
                    o.dispatchEvent(new Event('change', {view: window,bubbles: true}))
                }
                """
            )

    async def set_value(self, value: str) -> None:
        await self.tab.send(cdp.dom.set_node_value(node_id=self.node_id, value=value))

    async def set_text(self, value: str) -> None:
        if not self.node_type == 3:
            if self.child_node_count == 1:
                child_node = self.children[0]
                if not isinstance(child_node, type(self)):
                     pass
                await child_node.set_text(value)
                await self.update()
                return
            else:
                raise RuntimeError("could only set value of text nodes")
        await self.update()
        await self.tab.send(cdp.dom.set_node_value(node_id=self.node_id, value=value))

    async def get_html(self) -> str:
        return await self.tab.send(
            cdp.dom.get_outer_html(backend_node_id=self.backend_node_id)
        )

    async def get_js_attributes(self) -> ContraDict:
        from .._contradict import ContraDict
        return ContraDict(
            json.loads(
                await self.apply(
                    """
            function (e) {
                let o = {}
                for(let k in e){
                    o[k] = e[k]
                }
                return JSON.stringify(o)
            }
            """
                )
            )
        )

    def __await__(self) -> typing.Any:
        return self.update().__await__()

    def __call__(self, js_method: str) -> typing.Any:
        return self.apply(f"(e) => e['{js_method}']()")

    async def apply(
        self,
        js_function: str,
        return_by_value: bool = True,
        *,
        await_promise: bool = False,
    ) -> typing.Any:
        if not self.remote_object:
             setattr(self, '_remote_object', await self.tab.send(
                cdp.dom.resolve_node(backend_node_id=self.backend_node_id)
            ))

        result: typing.Tuple[
            cdp.runtime.RemoteObject, typing.Any
        ] = await self.tab.send(
            cdp.runtime.call_function_on(
                js_function,
                object_id=self.remote_object.object_id,
                arguments=[
                    cdp.runtime.CallArgument(object_id=self.remote_object.object_id)
                ],
                return_by_value=True,
                user_gesture=True,
                await_promise=await_promise,
            )
        )
        if result and result[0]:
            if return_by_value:
                return result[0].value
            return result[0]
        elif result[1]:
            return result[1]

    async def get_position(self, abs: bool = False) -> Position | None:
        if not self.remote_object or not self.parent or not self.object_id:
             setattr(self, '_remote_object', await self.tab.send(
                cdp.dom.resolve_node(backend_node_id=self.backend_node_id)
            ))
        try:
            quads = await self.tab.send(
                cdp.dom.get_content_quads(object_id=self.remote_object.object_id)
            )
            if not quads:
                raise Exception("could not find position for %s " % self)
            pos = Position(quads[0])
            if abs:
                scroll_y = (await self.tab.evaluate("window.scrollY")).value  # type: ignore
                scroll_x = (await self.tab.evaluate("window.scrollX")).value  # type: ignore
                abs_x = pos.left + scroll_x + (pos.width / 2)
                abs_y = pos.top + scroll_y + (pos.height / 2)
                pos.abs_x = abs_x
                pos.abs_y = abs_y
            return pos
        except:
            return None

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
        from ..element import Element # local import
        start_position = await self.get_position()
        if not start_position:
            logger.warning("could not find location for %s, not dragging", self)
            return
        start_point = start_position.center
        end_point = None
        if isinstance(destination, Element):
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

        # Use bezier for dragging too, reusing simple logic for now but improving steps
        # NOTE: mouse_drag is separate from click, could use same cubic_bezier logic
        # But for now, just keep the linear loop but with more noise/pauses if desired.
        # Given "human" priority, I should apply bezier here too.
        
        last_x, last_y = start_point
        target_x, target_y = end_point

        dist = math.hypot(target_x - last_x, target_y - last_y)
        if dist > 10:
             ux = (target_x - last_x) / dist
             uy = (target_y - last_y) / dist
             px = -uy
             py = ux
             deviation = min(dist/4, 100) * random.uniform(-1, 1)
             p1 = (last_x + (target_x - last_x)/3 + px * deviation, last_y + (target_y - last_y)/3 + py * deviation)
             p2 = (last_x + 2*(target_x - last_x)/3 + px * deviation, last_y + 2*(target_y - last_y)/3 + py * deviation)
        else:
             p1 = (last_x, last_y)
             p2 = (target_x, target_y)

        steps = max(30, int(dist / 5))

        await self.tab.send(
            cdp.input_.dispatch_mouse_event(
                "mousePressed",
                x=start_point[0],
                y=start_point[1],
                button=cdp.input_.MouseButton("left"),
            )
        )

        for i in range(1, steps + 1):
            t = i / steps
            t_eased = t * t * (3 - 2 * t)
            mx, my = cubic_bezier(t_eased, (last_x, last_y), p1, p2, (target_x, target_y))

            await self.tab.send(
                cdp.input_.dispatch_mouse_event(
                    "mouseMoved",
                    x=mx,
                    y=my,
                )
            )
            # Add drag-specific noise/pauses
            if random.random() > 0.95:
                await asyncio.sleep(random.uniform(0.001, 0.005))

        await self.tab.send(
            cdp.input_.dispatch_mouse_event(
                type_="mouseReleased",
                x=end_point[0],
                y=end_point[1],
                button=cdp.input_.MouseButton("left"),
            )
        )

    async def scroll_into_view(self) -> None:
        try:
            await self.tab.send(
                cdp.dom.scroll_into_view_if_needed(backend_node_id=self.backend_node_id)
            )
        except Exception as e:
            logger.debug("could not scroll into view: %s", e)
            return
