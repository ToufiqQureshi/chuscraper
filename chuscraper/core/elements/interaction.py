from __future__ import annotations
from .base import ElementMixin
from typing import TYPE_CHECKING, Literal, Any, Optional, Union, Tuple
import asyncio
import json
import logging
import typing
import random

from ... import cdp
from .. import util
from ..config import PathLike
from ..keys import KeyEvents, KeyPressEvent, SpecialKeys

if TYPE_CHECKING:
    from ..element import Element
    from .._contradict import ContraDict

logger = logging.getLogger(__name__)

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
    
    # We need to define _remote_object here or in base, it's used heavily
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
        """
        Updates the element's node information and remote object handle.
        Crucial for preventing 'Could not find node' errors after DOM changes.
        """
        if _node:
            doc = _node
        else:
            # We must enable DOM before fetching document to ensure node tracking
            await self.tab.send(cdp.dom.enable())
            doc = await self.tab.send(cdp.dom.get_document(-1, True))
        
        current_node = getattr(self, '_node')
        updated_node = util.filter_recurse(
            doc, lambda n: n.backend_node_id == current_node.backend_node_id
        )

        if updated_node:
            logger.debug(f"Node updated for element {self.node_name}")
            setattr(self, '_node', updated_node)
        else:
            # If still not found in tree, the node might be detached or in a different branch.
            # We attempt to describe the node directly via backend id as a last resort.
            try:
                describe_res = await self.tab.send(cdp.dom.describe_node(backend_node_id=current_node.backend_node_id))
                if describe_res:
                     setattr(self, '_node', describe_res)
            except Exception:
                logger.debug(f"Failed to resolve node {current_node.backend_node_id} even after refresh")

        setattr(self, '_tree', doc)

        # Ensure remote object is fresh
        try:
            new_remote_obj = await self.tab.send(
                cdp.dom.resolve_node(backend_node_id=getattr(self, '_node').backend_node_id)
            )
            setattr(self, '_remote_object', new_remote_obj)
        except Exception as e:
            logger.debug(f"Failed to resolve remote object for {self.node_name}: {e}")
        
        self.attrs.clear()
        if hasattr(self, '_make_attrs'):
            self._make_attrs() # type: ignore
            
        return self # type: ignore

    async def save_to_dom(self) -> None:
        """
        saves element to dom
        :return:
        :rtype:
        """
        # We need to set _remote_object
        ro = await self.tab.send(
            cdp.dom.resolve_node(backend_node_id=self.backend_node_id)
        )
        setattr(self, '_remote_object', ro)
        await self.tab.send(cdp.dom.set_outer_html(self.node_id, outer_html=str(self)))
        await self.update()

    async def remove_from_dom(self) -> None:
        """removes the element from dom"""
        await self.update()  # ensure we have latest node_id
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
        retry: Optional[bool] = None,
        flash: bool = False,
        **kwargs
    ) -> None:
        if flash:
            await self.flash(0.1, retry=retry)

        if mode in ("fast", "cdp"):
            await self.apply("(el) => el.click()", await_promise=True, retry=retry)
            return

        # Scroll into view before clicking if using mouse events
        await self.scroll_into_view()
        pos = await self.get_position(retry=retry)
        if not pos:
            # Fallback to fast click if position unknown
            return await self.click(mode="fast")

        target_x, target_y = pos.center
        
        if mode == "human":
            # Simple linear mouse path from last position to target
            last_x = getattr(self.tab, '_last_mouse_x', 0)
            last_y = getattr(self.tab, '_last_mouse_y', 0)
            
            # Generate a few mid-points for a slightly natural path
            steps = max(5, int(((target_x - last_x)**2 + (target_y - last_y)**2)**0.5 // 20))
            for i in range(1, steps + 1):
                mx = last_x + (target_x - last_x) * i / steps
                my = last_y + (target_y - last_y) * i / steps
                await self.tab.send(cdp.input_.dispatch_mouse_event(
                    type_="mouseMoved", x=mx, y=my
                ))
            
            # Click
            await self.tab.send(cdp.input_.dispatch_mouse_event(
                type_="mousePressed", x=target_x, y=target_y, button=cdp.input_.MouseButton(button), click_count=click_count
            ))
            await asyncio.sleep(random.uniform(0.05, 0.15))
            await self.tab.send(cdp.input_.dispatch_mouse_event(
                type_="mouseReleased", x=target_x, y=target_y, button=cdp.input_.MouseButton(button), click_count=click_count
            ))

    async def fill(self, text: str) -> None:
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

    async def send_file(self, *file_paths: PathLike, retry: Optional[bool] = None) -> None:
        if retry is None:
            config = self.tab.browser.config if self.tab.browser else None
            retry = getattr(config, "retry_enabled", False)

        file_paths_as_str = [str(p) for p in file_paths]
        try:
            await self.tab.send(
                cdp.dom.set_file_input_files(
                    files=[*file_paths_as_str],
                    backend_node_id=self.backend_node_id,
                    object_id=self.object_id,
                )
            )
        except Exception as e:
            from ..connection import ProtocolException
            if retry and isinstance(e, ProtocolException) and e.code == -32000:
                logger.debug(f"Retrying send_file() on {self.node_name} after stale object_id error")
                setattr(self, '_remote_object', None)
                await self.update()
                return await self.send_file(*file_paths, retry=False)
            raise e

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
                if not isinstance(child_node, type(self)): # Check against Element type via self type
                     # But self.children returns List[Element], so child_node IS Element
                     # The original code: if not isinstance(child_node, Element):
                     # keep it safe
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
        retry: Optional[bool] = None,
    ) -> typing.Any:
        if retry is None:
            config = self.tab.browser.config if self.tab.browser else None
            retry = getattr(config, "retry_enabled", False)

        if not self.remote_object:
             setattr(self, '_remote_object', await self.tab.send(
                cdp.dom.resolve_node(backend_node_id=self.backend_node_id)
            ))

        try:
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
            if result:
                if result[0]:
                    if return_by_value:
                        return result[0].value
                    return result[0]
                return result[1]
        except Exception as e:
            from ..connection import ProtocolException
            if retry and isinstance(e, ProtocolException) and e.code == -32000:
                logger.debug(f"Retrying apply() on {self.node_name} after stale object_id error")
                setattr(self, '_remote_object', None)  # Clear cache to force refresh
                await self.update()
                return await self.apply(js_function, return_by_value, await_promise=await_promise, retry=False)
            raise e

    async def get_position(self, abs: bool = False, retry: Optional[bool] = None) -> Position | None:
        if retry is None:
            config = self.tab.browser.config if self.tab.browser else None
            retry = getattr(config, "retry_enabled", False)

        if not self.remote_object or not self.object_id:
             try:
                 setattr(self, '_remote_object', await self.tab.send(
                    cdp.dom.resolve_node(backend_node_id=self.backend_node_id)
                ))
             except Exception as e:
                 logger.debug(f"Failed to resolve node for position: {e}")
                 return None
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
        except Exception as e:
            from ..connection import ProtocolException
            if retry and isinstance(e, ProtocolException) and e.code == -32000:
                logger.debug(f"Retrying get_position() on {self.node_name} after stale object_id error")
                setattr(self, '_remote_object', None)
                await self.update()
                return await self.get_position(abs=abs, retry=False)
            return None

    async def mouse_click(
        self,
        button: str = "left",
        buttons: typing.Optional[int] = 1,
        modifiers: typing.Optional[int] = 0,
        hold: bool = False,
        _until_event: typing.Optional[type] = None,
        retry: Optional[bool] = None,
    ) -> None:
        position = await self.get_position(retry=retry)
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
    async def mouse_move(self, retry: Optional[bool] = None) -> None:
        position = await self.get_position(retry=retry)
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

    async def hover(self, retry: Optional[bool] = None) -> None:
        """Alias for mouse_move to hover cursor over the element."""
        await self.mouse_move(retry=retry)

    async def mouse_drag(
        self,
        destination: typing.Union[Element, typing.Tuple[int, int]],
        relative: bool = False,
        steps: int = 1,
        retry: Optional[bool] = None,
    ) -> None:
        from ..element import Element # local import
        start_position = await self.get_position(retry=retry)
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

        from ..humanizer import Humanizer
        
        await self.tab.send(
            cdp.input_.dispatch_mouse_event(
                "mousePressed",
                x=start_point[0],
                y=start_point[1],
                button=cdp.input_.MouseButton("left"),
            )
        )

        num_steps = steps or max(10, int(((end_point[0] - start_point[0])**2 + (end_point[1] - start_point[1])**2)**0.5 // 10))
        for i in range(1, num_steps + 1):
            x = start_point[0] + (end_point[0] - start_point[0]) * i / num_steps
            y = start_point[1] + (end_point[1] - start_point[1]) * i / num_steps
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

    async def scroll_into_view(self) -> None:
        try:
            await self.tab.send(
                cdp.dom.scroll_into_view_if_needed(backend_node_id=self.backend_node_id)
            )
        except Exception as e:
            logger.debug("could not scroll into view: %s", e)
            return

