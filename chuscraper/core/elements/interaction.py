from __future__ import annotations
from .base import ElementMixin
from typing import TYPE_CHECKING, Literal, Any, Optional, Union, Tuple
import asyncio
import base64
import datetime
import json
import logging
import pathlib
import secrets
import typing
import urllib.parse
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
        # This implementation requires access to self._node, self._tree, self._remote_object
        # It updates them logic implies it should be in the main Element class OR 
        # we define the logic here and Element uses it. 
        # Given it relies on internal state _node/_tree extensively, maybe keep in Element?
        # But wait, query methods call update().
        # Let's keep logic here but assume setters/properties exist or direct access 
        # (in python we can access protected members)
        
        # NOTE: For mixin refactoring, update() is central. I will implement it here using self._node etc
        # assuming the main class provides them.
        
        if _node:
            doc = _node
        else:
            doc = await self.tab.send(cdp.dom.get_document(-1, True))
        
        # We need self._node access. 
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
        # call self._make_attrs()
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

    async def scroll_into_view(self) -> None:
        try:
            await self.tab.send(
                cdp.dom.scroll_into_view_if_needed(backend_node_id=self.backend_node_id)
            )
        except Exception as e:
            logger.debug("could not scroll into view: %s", e)
            return

    async def screenshot_b64(
        self,
        format: str = "jpeg",
        scale: typing.Optional[typing.Union[int, float]] = 1,
    ) -> str:
        pos = await self.get_position()
        if not pos:
            raise RuntimeError(
                "could not determine position of element. probably because it's not in view, or hidden"
            )
        viewport = pos.to_viewport(float(scale if scale else 1))
        await self.tab.sleep()

        data = await self.tab.send(
            cdp.page.capture_screenshot(
                format, clip=viewport, capture_beyond_viewport=True
            )
        )

        if not data:
            from ..connection import ProtocolException

            raise ProtocolException(
                "could not take screenshot. most possible cause is the page has not finished loading yet."
            )

        return data

    async def save_screenshot(
        self,
        filename: typing.Optional[PathLike] = "auto",
        format: str = "jpeg",
        scale: typing.Optional[typing.Union[int, float]] = 1,
    ) -> str:
        await self.tab.sleep()

        if not filename or filename == "auto":
            parsed = urllib.parse.urlparse(self.tab.target.url)  # type: ignore
            parts = parsed.path.split("/")
            last_part = parts[-1]
            last_part = last_part.rsplit("?", 1)[0]
            dt_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            candidate = f"{parsed.hostname}__{last_part}_{dt_str}"
            ext = ""
            if format.lower() in ["jpg", "jpeg"]:
                ext = ".jpg"
            elif format.lower() in ["png"]:
                ext = ".png"
            path = pathlib.Path(candidate + ext)
        else:
            path = pathlib.Path(filename)

        path.parent.mkdir(parents=True, exist_ok=True)

        data = await self.screenshot_b64(format, scale)

        data_bytes = base64.b64decode(data)
        path.write_bytes(data_bytes)
        return str(path)

    async def flash(self, duration: typing.Union[float, int] = 0.5) -> None:
        from ..connection import ProtocolException

        if not self.remote_object:
            try:
                 setattr(self, '_remote_object', await self.tab.send(
                    cdp.dom.resolve_node(backend_node_id=self.backend_node_id)
                ))
            except ProtocolException:
                return
        if not self.remote_object or not self.remote_object.object_id:
            raise ValueError("could not resolve object id for %s" % self)
        pos = await self.get_position()
        if pos is None:
            logger.warning("flash() : could not determine position")
            return

        style = (
            "position:absolute;z-index:99999999;padding:0;margin:0;"
            "left:{:.1f}px; top: {:.1f}px;"
            "opacity:1;"
            "width:16px;height:16px;border-radius:50%;background:red;"
            "animation:show-pointer-ani {:.2f}s ease 1;"
        ).format(
            pos.center[0] - 8,  # -8 to account for drawn circle itself (w,h)
            pos.center[1] - 8,
            duration,
        )
        script = (
            """
            (targetElement) => {{
                var css = document.styleSheets[0];
                for( let css of [...document.styleSheets]) {{
                    try {{
                        css.insertRule(`
                        @keyframes show-pointer-ani {{
                              0% {{ opacity: 1; transform: scale(2, 2);}}
                              25% {{ transform: scale(5,5) }}
                              50% {{ transform: scale(3, 3);}}
                              75%: {{ transform: scale(2,2) }}
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
            }}
            """.format(
                style,
                secrets.token_hex(8),
                int(duration * 1000),
            )
            .replace("  ", "")
            .replace("\n", "")
        )

        arguments = [cdp.runtime.CallArgument(object_id=self.remote_object.object_id)]
        await self.tab.send(
            cdp.runtime.call_function_on(
                script,
                object_id=self.remote_object.object_id,
                arguments=arguments,
                await_promise=True,
                user_gesture=True,
            )
        )

    async def highlight_overlay(self) -> None:
        if getattr(self, "_is_highlighted", False):
            del self._is_highlighted
            await self.tab.send(cdp.overlay.hide_highlight())
            await self.tab.send(cdp.dom.disable())
            await self.tab.send(cdp.overlay.disable())
            return
        await self.tab.send(cdp.dom.enable())
        await self.tab.send(cdp.overlay.enable())
        conf = cdp.overlay.HighlightConfig(
            show_info=True, show_extension_lines=True, show_styles=True
        )
        await self.tab.send(
            cdp.overlay.highlight_node(
                highlight_config=conf, backend_node_id=self.backend_node_id
            )
        )
        setattr(self, "_is_highlighted", 1)

    async def record_video(
        self,
        filename: typing.Optional[str] = None,
        folder: typing.Optional[str] = None,
        duration: typing.Optional[typing.Union[int, float]] = None,
    ) -> None:
        if self.node_name != "VIDEO":
            raise RuntimeError(
                "record_video can only be called on html5 video elements"
            )
        if not folder:
            directory_path = pathlib.Path.cwd() / "downloads"
        else:
            directory_path = pathlib.Path(folder)

        directory_path.mkdir(exist_ok=True)
        await self.tab.send(
            cdp.browser.set_download_behavior(
                "allow", download_path=str(directory_path)
            )
        )
        await self("pause")
        await self.apply(
            """
            function extractVid(vid) {{

                      var duration = {duration:.1f};
                      var stream = vid.captureStream();
                      var mr = new MediaRecorder(stream, {{audio:true, video:true}})
                      mr.ondataavailable  = function(e) {{
                          vid['_recording'] = false
                          var blob = e.data;
                          f = new File([blob], {{name: {filename}, type:'octet/stream'}});
                          var objectUrl = URL.createObjectURL(f);
                          var link = document.createElement('a');
                          link.setAttribute('href', objectUrl)
                          link.setAttribute('download', {filename})
                          link.style.display = 'none'

                          document.body.appendChild(link)

                          link.click()

                          document.body.removeChild(link)
                       }}

                       mr.start()
                       vid.addEventListener('ended' , (e) => mr.stop())
                       vid.addEventListener('pause' , (e) => mr.stop())
                       vid.addEventListener('abort', (e) => mr.stop())


                       if ( duration ) {{
                            setTimeout(() => {{ vid.pause(); vid.play() }}, duration);
                       }}
                       vid['_recording'] = true
                  ;}}

            """.format(
                filename=f'"{filename}"' if filename else 'document.title + ".mp4"',
                duration=int(duration * 1000) if duration else 0,
            )
        )
        await self("play")
        await self.tab

    async def is_recording(self) -> bool:
        return await self.apply('(vid) => vid["_recording"]')  # type: ignore
