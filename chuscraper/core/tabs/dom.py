from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING, List, Optional, Union, Any, cast
import asyncio
import logging
import json
from .. import element
from .. import util
from ... import cdp
from ..connection import ProtocolException

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..tab import Tab
    from ..element import Element

class DomMixin(TabMixin):
    async def xpath(self, xpath: str) -> List[Element]:
        """
        Evaluate an XPath expression and return matching elements.
        Supports JS fallback for broken DOM agents.
        """
        # Ensure DOM agent enabled
        try: await self.send(cdp.dom.enable())
        except: pass

        # 1. JS Fallback (Often more reliable for basic XPath search on stable pages)
        try:
            js_meta_code = f"""
            (function() {{
                let results = document.evaluate({json.dumps(xpath)}, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                let nodes = [];
                for(let i=0; i<results.snapshotLength; i++) {{
                    let el = results.snapshotItem(i);
                    let attrs = [];
                    if (el.attributes) {{ for (let attr of el.attributes) {{ attrs.push(attr.name); attrs.push(attr.value); }} }}
                    nodes.push({{
                        nodeName: el.tagName || el.nodeName,
                        nodeType: el.nodeType,
                        attributes: attrs,
                        textContent: el.textContent
                    }});
                    if (nodes.length >= 100) break;
                }}
                return nodes;
            }})()
            """
            res, _ = await self.send(cdp.runtime.evaluate(js_meta_code, return_by_value=True))
            if res and res.value:
                doc = await self.send(cdp.dom.get_document(-1, True))
                items = []
                for idx, val in enumerate(res.value):
                    synthetic_node = cdp.dom.Node(
                        node_id=cdp.dom.NodeId(-1),
                        backend_node_id=cdp.dom.BackendNodeId(-1),
                        node_type=val.get("nodeType", 1),
                        node_name=val.get("nodeName", ""),
                        local_name=val.get("nodeName", "").lower(),
                        node_value=val.get("textContent", ""),
                        attributes=val.get("attributes", [])
                    )
                    elem = element.create(synthetic_node, self.tab, doc)
                    if elem:
                         setattr(elem, '_selector', f"xpath:{xpath}")
                         setattr(elem, '_index', idx)
                         try:
                             js_obj_code = f"document.evaluate({json.dumps(xpath)}, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null).snapshotItem({idx})"
                             obj_res, _ = await self.send(cdp.runtime.evaluate(js_obj_code))
                             if obj_res and obj_res.object_id:
                                 elem._remote_object = obj_res
                         except: pass
                         items.append(elem)
                if items: return items
        except Exception as e:
            logger.debug(f"JS XPath resolution failed for {xpath}: {e}")

        # 2. Native CDP Attempt
        try:
            doc = await self.send(cdp.dom.get_document(-1, True))
            search_id, result_count = await self.send(cdp.dom.perform_search(xpath, include_user_agent_shadow_dom=True))
            if result_count > 0:
                node_ids = await self.send(cdp.dom.get_search_results(search_id, 0, result_count))
                await self.send(cdp.dom.discard_search_results(search_id))
                items = []
                for nid in node_ids:
                    node_info = await self.send(cdp.dom.describe_node(node_id=nid, depth=-1, pierce=True))
                    if node_info:
                        elem = element.create(node_info, self.tab, doc)
                        if elem: items.append(elem)
                return items
        except Exception as e:
            logger.debug(f"Native XPath search failed for {xpath}: {e}")

        return []

    async def select(self, selector: str, timeout: Optional[float] = None) -> Element:
        """Finds a single element with aggressive retry loops (5 attempts)."""
        t_out = timeout if timeout is not None else self.timeout
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        
        attempts = 0
        while True:
            attempts += 1
            try:
                item = await self.tab.query_selector(selector)
                if item:
                    return item
            except Exception as e:
                logger.debug(f"Select attempt {attempts} failed: {e}")

            if loop.time() - start_time > t_out and attempts >= 5:
                raise asyncio.TimeoutError(f"Timeout ({t_out}s) waiting for element: '{selector}'")

            await asyncio.sleep(min(0.5, t_out / 5))

    async def select_all(self, selector: str, timeout: Optional[float] = None, include_frames: bool = False, **kwargs) -> List[Element]:
        """Finds multiple elements with aggressive retry loops (5 attempts)."""
        t_out = timeout if timeout is not None else self.timeout
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        
        attempts = 0
        while True:
            attempts += 1
            try:
                items = await self.tab.query_selector_all(selector)
                if items:
                    return items
            except Exception as e:
                logger.debug(f"Select_all attempt {attempts} failed: {e}")

            if (loop.time() - start_time > t_out) and (attempts >= 5):
                return []

            await asyncio.sleep(min(0.5, t_out / 5))

    async def find(self, text: str, best_match: bool = True, timeout: Optional[float] = None) -> Element:
        """Finds element by text match."""
        t_out = timeout if timeout is not None else self.timeout
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        
        while True:
            items = await self.tab.find_elements_by_text(text)
            if items:
                if best_match and len(items) > 1:
                    return min(items, key=lambda x: abs(len(x.text_all or "") - len(text)))
                return items[0]

            if loop.time() - start_time > t_out:
                raise asyncio.TimeoutError(f"Timeout ({t_out}s) waiting for text: '{text}'")

            await asyncio.sleep(0.5)

    async def select_text(self, selector: str, timeout: Union[int, float] = 10) -> str | None:
        """One-liner to find an element and return its inner text."""
        el = await self.select(selector, timeout=timeout)
        return el.text_all if el else None

    async def query_selector_all(
        self,
        selector: str,
        _node: cdp.dom.Node | Element | None = None,
    ) -> List[Element]:
        """
        Production Grade query_selector_all with multi-stage resolution.
        """
        items = []
        selector = selector.strip()
        
        # 1. XPath Shortcut
        is_xpath = selector.startswith("xpath:")
        clean_selector = selector[6:] if is_xpath else selector
        if is_xpath:
            return await self.xpath(clean_selector)

        # 2. Native CDP Attempt
        try:
            await self.send(cdp.dom.enable())
            doc = await self.send(cdp.dom.get_document(-1, True))
            node_ids = await self.send(cdp.dom.query_selector_all(doc.node_id, clean_selector))
            if node_ids:
                for nid in node_ids:
                    node_info = await self.send(cdp.dom.describe_node(node_id=nid, depth=-1, pierce=True))
                    if node_info:
                        elem = element.create(node_info, self.tab, doc)
                        if elem: items.append(elem)
                if items: return items
        except Exception as e:
            logger.debug(f"query_selector_all Native failed for {selector}: {e}")

        # 3. JS-to-CDP Fallback
        try:
            js_map_code = f"(function() {{ return document.querySelectorAll({json.dumps(clean_selector)}).length; }})()"
            res, _ = await self.send(cdp.runtime.evaluate(js_map_code, return_by_value=True))
            if res and res.value:
                count = int(res.value)
                if count > 0:
                    doc = await self.send(cdp.dom.get_document(-1, True))
                    for i in range(count):
                        try:
                            js_obj_code = f"document.querySelectorAll({json.dumps(clean_selector)})[{i}]"
                            obj_res, _ = await self.send(cdp.runtime.evaluate(js_obj_code))
                            if obj_res and obj_res.object_id:
                                node_id = await self.send(cdp.dom.request_node(object_id=obj_res.object_id))
                                node_info = await self.send(cdp.dom.describe_node(node_id=node_id, depth=-1, pierce=True))
                                elem = element.create(node_info, self.tab, doc)
                                if elem:
                                    elem._remote_object = obj_res
                                    items.append(elem)
                        except: pass
                if items: return items
        except Exception as e:
            logger.debug(f"query_selector_all JS-CDP failed for {selector}: {e}")

        # 4. Synthetic Node Fallback (Last resort)
        try:
            js_meta_code = f"""
            (function() {{
                let els = document.querySelectorAll({json.dumps(clean_selector)});
                let results = [];
                for(let el of els) {{
                    let attrs = [];
                    if (el.attributes) {{ for (let attr of el.attributes) {{ attrs.push(attr.name); attrs.push(attr.value); }} }}
                    results.push({{
                        nodeName: el.tagName,
                        nodeType: el.nodeType,
                        attributes: attrs,
                        textContent: el.textContent
                    }});
                }}
                return results;
            }})()
            """
            res, _ = await self.send(cdp.runtime.evaluate(js_meta_code, return_by_value=True))
            if res and res.value:
                doc = await self.send(cdp.dom.get_document(-1, True))
                for idx, val in enumerate(res.value):
                    synthetic_node = cdp.dom.Node(
                        node_id=cdp.dom.NodeId(-1),
                        backend_node_id=cdp.dom.BackendNodeId(-1),
                        node_type=val.get("nodeType", 1),
                        node_name=val.get("nodeName", ""),
                        local_name=val.get("nodeName", "").lower(),
                        node_value=val.get("textContent", ""),
                        attributes=val.get("attributes", [])
                    )
                    elem = element.create(synthetic_node, self.tab, doc)
                    if elem:
                        setattr(elem, '_selector', clean_selector)
                        setattr(elem, '_index', idx)
                        items.append(elem)
        except Exception as e:
            logger.debug(f"query_selector_all synthetic fallback failed for {selector}: {e}")
            
        return items

    async def query_selector(
        self,
        selector: str,
        _node: Optional[Union[cdp.dom.Node, Element]] = None,
    ) -> Element | None:
        """
        Production Grade query_selector with multi-stage resolution.
        """
        selector = selector.strip()
        
        # 1. XPath detection
        is_xpath = selector.startswith("xpath:")
        clean_selector = selector[6:] if is_xpath else selector

        # 2. Native CDP Attempt
        try:
            await self.send(cdp.dom.enable())
            doc = await self.send(cdp.dom.get_document(-1, True))
            
            if is_xpath:
                results = await self.xpath(clean_selector)
                if results: return results[0]
            else:
                node_id = await self.send(cdp.dom.query_selector(doc.node_id, clean_selector))
                if node_id and node_id != 0:
                    node_info = await self.send(cdp.dom.describe_node(node_id=node_id, depth=-1, pierce=True))
                    if node_info:
                        return element.create(node_info, self.tab, doc)
        except Exception as e:
            logger.debug(f"Native CDP query failed for {selector}: {e}")

        # 3. JS-to-CDP Resolution
        try:
            if is_xpath:
                js_code = f"document.evaluate({json.dumps(clean_selector)}, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue"
            else:
                js_code = f"document.querySelector({json.dumps(clean_selector)})"
            
            res, _ = await self.send(cdp.runtime.evaluate(js_code))
            if res and res.object_id:
                try:
                    node_id = await self.send(cdp.dom.request_node(object_id=res.object_id))
                    node_info = await self.send(cdp.dom.describe_node(node_id=node_id, depth=-1, pierce=True))
                    doc = await self.send(cdp.dom.get_document(-1, True))
                    elem = element.create(node_info, self.tab, doc)
                    if elem:
                        elem._remote_object = res
                        return elem
                except: pass
        except Exception as e:
            logger.debug(f"JS-CDP resolution failed for {selector}: {e}")

        # 4. Synthetic Node Fallback
        try:
            if not is_xpath:
                js_meta_code = f"""
                (function() {{
                    let el = document.querySelector({json.dumps(clean_selector)});
                    if (!el) return null;
                    let attrs = [];
                    if (el.attributes) {{ for (let attr of el.attributes) {{ attrs.push(attr.name); attrs.push(attr.value); }} }}
                    return {{
                        nodeName: el.tagName,
                        nodeType: el.nodeType,
                        attributes: attrs,
                        textContent: el.textContent
                    }};
                }})()
                """
                meta_res, _ = await self.send(cdp.runtime.evaluate(js_meta_code, return_by_value=True))
                if meta_res and meta_res.value:
                    val = meta_res.value
                    synthetic_node = cdp.dom.Node(
                        node_id=cdp.dom.NodeId(-1),
                        backend_node_id=cdp.dom.BackendNodeId(-1),
                        node_type=val.get("nodeType", 1),
                        node_name=val.get("nodeName", ""),
                        local_name=val.get("nodeName", "").lower(),
                        node_value=val.get("textContent", ""),
                        attributes=val.get("attributes", [])
                    )
                    doc = await self.send(cdp.dom.get_document(-1, True))
                    elem = element.create(synthetic_node, self.tab, doc)
                    if elem:
                        setattr(elem, '_selector', clean_selector)
                        obj_res, _ = await self.send(cdp.runtime.evaluate(js_code, return_by_value=False))
                        if obj_res and obj_res.object_id:
                            elem._remote_object = obj_res
                        return elem
        except Exception as e:
            logger.debug(f"Synthetic fallback failed for {selector}: {e}")

        return None

    async def resolve_node(self, backend_node_id: int) -> Element:
        doc = await self.send(cdp.dom.get_document(-1, True))
        try:
            node = util.filter_recurse(doc, lambda n: n.backend_node_id == backend_node_id)
            if node:
                return element.create(node, self.tab, doc)
            
            obj = await self.send(cdp.dom.resolve_node(backend_node_id=backend_node_id))
            node_id = await self.send(cdp.dom.request_node(object_id=obj.object_id))
            
            doc = await self.send(cdp.dom.get_document(-1, True))
            node = util.filter_recurse(doc, lambda n: n.node_id == node_id)
            if node:
                return element.create(node, self.tab, doc)
                
            raise ProtocolException("Could not resolve backend node into an element")
        finally:
            pass

    async def find_elements_by_text(
        self,
        text: str,
        tag_hint: Optional[str] = None,
    ) -> list[Element]:
        """
        Returns elements matching text using multi-stage resolution.
        """
        text = text.strip()
        items = []

        # 1. JS Fallback (Reliable & Fast)
        try:
            # We use an XPath that is case-insensitive-ish and robust
            xpath_query = f"//*[contains(text(), {json.dumps(text)}) or contains(@value, {json.dumps(text)}) or contains(@placeholder, {json.dumps(text)})]"
            js_meta_code = f"""
            (function() {{
                let results = document.evaluate({json.dumps(xpath_query)}, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                let nodes = [];
                for(let i=0; i<results.snapshotLength; i++) {{
                    let el = results.snapshotItem(i);
                    let attrs = [];
                    if (el.attributes) {{ for (let attr of el.attributes) {{ attrs.push(attr.name); attrs.push(attr.value); }} }}
                    nodes.push({{
                        nodeName: el.tagName || el.nodeName,
                        nodeType: el.nodeType,
                        attributes: attrs,
                        textContent: el.textContent
                    }});
                    if (nodes.length >= 50) break;
                }}
                return nodes;
            }})()
            """
            res, _ = await self.send(cdp.runtime.evaluate(js_meta_code, return_by_value=True))
            if res and res.value:
                doc = await self.send(cdp.dom.get_document(-1, True))
                for idx, val in enumerate(res.value):
                    synthetic_node = cdp.dom.Node(
                        node_id=cdp.dom.NodeId(-1),
                        backend_node_id=cdp.dom.BackendNodeId(-1),
                        node_type=val.get("nodeType", 1),
                        node_name=val.get("nodeName", ""),
                        local_name=val.get("nodeName", "").lower(),
                        node_value=val.get("textContent", ""),
                        attributes=val.get("attributes", [])
                    )
                    elem = element.create(synthetic_node, self.tab, doc)
                    if elem:
                         setattr(elem, '_selector', f"text:{text}")
                         setattr(elem, '_index', idx)
                         try:
                             js_obj_code = f"document.evaluate({json.dumps(xpath_query)}, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null).snapshotItem({idx})"
                             obj_res, _ = await self.send(cdp.runtime.evaluate(js_obj_code))
                             if obj_res and obj_res.object_id:
                                 elem._remote_object = obj_res
                         except: pass
                         items.append(elem)
                if items: return items
        except Exception as e:
            logger.debug(f"JS find by text failed for {text}: {e}")

        # 2. Native CDP Attempt
        try:
            await self.send(cdp.dom.enable())
            doc = await self.send(cdp.dom.get_document(-1, True))
            search_id, nresult = await self.send(cdp.dom.perform_search(text, True))
            if nresult:
                node_ids = await self.send(cdp.dom.get_search_results(search_id, 0, nresult))
                await self.send(cdp.dom.discard_search_results(search_id))
                for nid in node_ids:
                    try:
                        node_info = await self.send(cdp.dom.describe_node(node_id=nid, depth=-1, pierce=True))
                        elem = element.create(node_info, self.tab, doc)
                        if elem:
                            if elem.node_type == 3: # Text node
                                items.append(elem.parent or elem)
                            else:
                                items.append(elem)
                    except: continue
                if items: return items
        except Exception as e:
            logger.debug(f"Native find by text failed for {text}: {e}")

        return items

    async def find_element_by_text(
        self,
        text: str,
        best_match: Optional[bool] = False,
        return_enclosing_element: Optional[bool] = True,
    ) -> Element | None:
        """
        finds and returns the first element containing <text>, or best match
        """
        items = await self.find_elements_by_text(text)
        try:
            if not items:
                return None
            if best_match:
                closest_by_length = min(
                    items, key=lambda el: abs(len(text) - len(el.text_all))
                )
                elem = closest_by_length or items[0]

                return elem
            else:
                for elem in items:
                    if elem:
                        return elem
        finally:
            pass

        return None
