from __future__ import annotations
from .base import ElementMixin, Position
from typing import TYPE_CHECKING, Literal, Any, Optional, Union, Tuple
import asyncio
import logging
import json
import secrets
import typing
from ... import cdp
from .. import util

if TYPE_CHECKING:
    from ..element import Element
    from .._contradict import ContraDict

logger = logging.getLogger(__name__)

class ElementInteractionMixin(ElementMixin):
    """Mixin for Core Element lifecycle and DOM interaction."""
    
    _remote_object: cdp.runtime.RemoteObject | None

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
        """
        saves element to dom
        :return:
        :rtype:
        """
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

    async def scroll_into_view(self) -> None:
        try:
            await self.tab.send(
                cdp.dom.scroll_into_view_if_needed(backend_node_id=self.backend_node_id)
            )
        except Exception as e:
            logger.debug("could not scroll into view: %s", e)
            return
