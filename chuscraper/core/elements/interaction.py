from __future__ import annotations
from .base import ElementMixin
from typing import TYPE_CHECKING, Literal, Any, Optional, Union, Tuple
import asyncio
import json
import logging
import typing
import random
import re

from ... import cdp
from .. import util
from ..config import PathLike
from ..keys import KeyEvents, KeyPressEvent, SpecialKeys
from ..connection import ProtocolException

if TYPE_CHECKING:
    from ..element import Element
    from .._contradict import ContraDict

logger = logging.getLogger(__name__)

class Position(cdp.dom.Quad):
    def __init__(self, points: list[float]):
        super().__init__(points)
        (self.left, self.top, self.right, self.top, self.right, self.bottom, self.left, self.bottom) = points
        self.abs_x, self.abs_y = 0, 0
        self.x, self.y = self.left, self.top
        self.height, self.width = (self.bottom - self.top, self.right - self.left)
        self.center = (self.left + (self.width / 2), self.top + (self.height / 2))

    def to_viewport(self, scale: float = 1) -> cdp.page.Viewport:
        return cdp.page.Viewport(x=self.x, y=self.y, width=self.width, height=self.height, scale=scale)

class ElementInteractionMixin(ElementMixin):
    _remote_object: cdp.runtime.RemoteObject | None

    @property
    def object_id(self) -> cdp.runtime.RemoteObjectId | None:
        return self._remote_object.object_id if self._remote_object else None
    
    @property
    def remote_object(self) -> cdp.runtime.RemoteObject | None:
        return self._remote_object

    async def update(self, _node: cdp.dom.Node | None = None) -> Element:
        bid = int(self.backend_node_id)
        if bid <= 0:
            await self._re_evaluate_synthetic()
            return self # type: ignore

        try:
            await self.tab.send(cdp.dom.enable())
            doc = _node or await self.tab.send(cdp.dom.get_document(-1, True))
            current_node = getattr(self, "_node")
            updated_node = util.filter_recurse(doc, lambda n: n.backend_node_id == current_node.backend_node_id)
            if updated_node: setattr(self, "_node", updated_node)
            setattr(self, "_tree", doc)

            # Refresh remote object
            self._remote_object = None
            try:
                ro = await self.tab.send(cdp.dom.resolve_node(backend_node_id=bid))
                setattr(self, "_remote_object", ro)
            except: pass

            self.attrs.clear()
            self._make_attrs()
        except: pass
        return self # type: ignore

    def _get_synthetic_selector_js(self) -> str | None:
        sel = getattr(self, "_selector", None)
        if not sel: return None
        idx = getattr(self, "_index", 0) or 0
        if sel.startswith("xpath:"):
            q = sel[6:]
            return f"document.evaluate({json.dumps(q)}, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null).snapshotItem({idx})"
        if sel.startswith("text:"):
            q = sel[5:]
            xq = f"//*[contains(text(), {json.dumps(q)}) or contains(@value, {json.dumps(q)}) or contains(@placeholder, {json.dumps(q)})]"
            return f"document.evaluate({json.dumps(xq)}, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null).snapshotItem({idx})"
        return f"document.querySelectorAll({json.dumps(sel)})[{idx}]"

    async def _re_evaluate_synthetic(self) -> bool:
        js = self._get_synthetic_selector_js()
        if not js: return False
        self._remote_object = None
        try:
            obj, _ = await self.tab.send(cdp.runtime.evaluate(js, return_by_value=False))
            if obj and obj.object_id:
                setattr(self, "_remote_object", obj)
                return True
        except: pass
        return False

    async def click(self, mode: Literal["human", "fast", "cdp"] = "human", button: str = "left", click_count: int = 1, retry: bool = True, **kwargs) -> None:
        if mode == "cdp": return await self.apply("(el) => el.click()", retry=retry)
        if mode == "fast":
            try: await self.flash(0.1, retry=retry)
            except: pass
            return await self.apply("(el) => el.click()", retry=retry)

        await self.scroll_into_view()
        pos = await self.get_position(retry=retry)
        if not pos: return await self.apply("(el) => el.click()", retry=retry)
        cx, cy = pos.center
        await self.tab.send(cdp.input_.dispatch_mouse_event("mousePressed", x=cx, y=cy, button=cdp.input_.MouseButton(button), click_count=click_count))
        await asyncio.sleep(random.uniform(0.05, 0.1))
        await self.tab.send(cdp.input_.dispatch_mouse_event("mouseReleased", x=cx, y=cy, button=cdp.input_.MouseButton(button), click_count=click_count))

    async def apply(self, js: str, return_by_value: bool = True, await_promise: bool = False, retry: bool = True) -> Any:
        bid = int(self.backend_node_id)
        fcode = self._get_synthetic_selector_js()
        
        def wrap_js(code: str) -> str:
            if not (code.strip().startswith("function") or "=>" in code):
                if re.match(r"^[a-zA-Z0-9_.]+(\(\))?$", code.strip()):
                    m = code.strip()[:-2] if code.strip().endswith("()") else code.strip()
                    return f"(el) => el['{m}']()" if code.strip().endswith("()") else f"(el) => el['{m}']"
                return f"(el) => {{ const element=el, e=el; return ({code})(el); }}"
            return code

        # Logic 1: Use synthetic JS path if node is synthetic OR if CDP path fails
        async def try_js_path():
            if not fcode: return None, False
            func = wrap_js(js)
            script = f"(function(el) {{ if (!el) return null; return ({func})(el); }})({fcode})"
            try:
                res, err = await self.tab.send(cdp.runtime.evaluate(script, user_gesture=True, await_promise=await_promise, return_by_value=return_by_value))
                if err: return None, False
                return (res.value if return_by_value else res), True
            except: return None, False

        if bid <= 0:
            val, ok = await try_js_path()
            if ok: return val
            if retry: return await self.apply(js, return_by_value, await_promise, False)
            raise ProtocolException("JS fallback failed for synthetic node")

        # Logic 2: Standard CDP Path
        if not self.remote_object:
            try: self._remote_object = await self.tab.send(cdp.dom.resolve_node(backend_node_id=bid))
            except: pass

        if not self.remote_object or not self.remote_object.object_id:
            val, ok = await try_js_path()
            if ok: return val
            raise ValueError(f"Could not resolve object for {self}")

        try:
            res = await self.tab.send(cdp.runtime.call_function_on(js, object_id=self.remote_object.object_id, arguments=[cdp.runtime.CallArgument(object_id=self.remote_object.object_id)], return_by_value=return_by_value, user_gesture=True, await_promise=await_promise))
            if res:
                if len(res) > 0 and res[0]: return res[0].value if return_by_value else res[0]
                return None # undefined
        except Exception as e:
            if retry and (("-32000" in str(e)) or ("id" in str(e))):
                logger.debug(f"Object expired for {self.node_name}, re-resolving...")
                await self.update()
                return await self.apply(js, return_by_value, await_promise, False)

            # Final fallback to JS path if CDP fails with non-expiration error
            val, ok = await try_js_path()
            if ok: return val
            raise e

    async def get_html(self) -> str:
        bid = int(self.backend_node_id)
        if bid > 0:
            try: return await self.tab.send(cdp.dom.get_outer_html(backend_node_id=bid))
            except: pass
        return await self.apply("(el) => el.outerHTML") or ""

    async def get_position(self, abs: bool = False, retry: bool = True) -> Position | None:
        bid = int(self.backend_node_id)
        if bid <= 0:
            try:
                r = await self.apply("(el) => { const b = el.getBoundingClientRect(); return { q: [b.left, b.top, b.right, b.top, b.right, b.bottom, b.left, b.bottom], sx: window.scrollX, sy: window.scrollY }; }", retry=retry)
                if r:
                    p = Position(r["q"])
                    if abs: p.abs_x, p.abs_y = p.left + r["sx"] + p.width/2, p.top + r["sy"] + p.height/2
                    return p
            except: pass
            return None
        if not self.remote_object or not self.object_id:
            try: self._remote_object = await self.tab.send(cdp.dom.resolve_node(backend_node_id=bid))
            except: pass
        if not self.remote_object or not self.object_id: return None
        try:
            qs = await self.tab.send(cdp.dom.get_content_quads(object_id=self.object_id))
            if not qs: return None
            p = Position(qs[0])
            if abs:
                sr = await self.tab.evaluate("({x: window.scrollX, y: window.scrollY})")
                if sr: p.abs_x, p.abs_y = p.left + sr["x"] + p.width/2, p.top + sr["y"] + p.height/2
            return p
        except Exception as e:
            if retry and (("-32000" in str(e)) or ("id" in str(e))):
                await self.update()
                return await self.get_position(abs, False)
            return None

    async def fill(self, text: str, retry: bool = True) -> None:
        await self.apply("(el) => el.focus()", retry=retry)
        await self.apply('function(e){ e.value = "" }', retry=retry)
        for c in text: await self.tab.send(cdp.input_.dispatch_key_event(**KeyEvents.from_text(c, KeyPressEvent.CHAR)[0]))

    async def scroll_into_view(self) -> None:
        bid = int(self.backend_node_id)
        if bid <= 0: await self.apply("(el) => el.scrollIntoView({behavior:'auto', block:'center'})")
        else:
            try: await self.tab.send(cdp.dom.scroll_into_view_if_needed(backend_node_id=bid))
            except: await self.apply("(el) => el.scrollIntoView({behavior:'auto', block:'center'})")

    async def focus(self) -> None: await self.apply("(el) => el.focus()")
    async def get_js_attributes(self) -> ContraDict:
        from .._contradict import ContraDict
        return ContraDict(json.loads(await self.apply("function(e){let o={};for(let k in e)o[k]=e[k];return JSON.stringify(o)}")))
    async def save_to_dom(self) -> None:
        bid = int(self.backend_node_id)
        if bid <= 0: raise RuntimeError("Cannot save synthetic")
        await self.tab.send(cdp.dom.set_outer_html(self.node_id, outer_html=str(self)))
        await self.update()
    async def remove_from_dom(self) -> None:
        await self.update()
        bid = int(self.backend_node_id)
        if self.tree and bid > 0:
            node = util.filter_recurse(self.tree, lambda n: n.backend_node_id == bid)
            if node: await self.tab.send(cdp.dom.remove_node(node.node_id))
