from __future__ import annotations
from .base import TabMixin
from typing import TYPE_CHECKING, List, Optional, Union, Any, cast
from .. import element
from .. import util
from ... import cdp
from ..connection import ProtocolException

if TYPE_CHECKING:
    from ..tab import Tab
    from ..element import Element

class DomMixin(TabMixin):
    async def select(self, selector: str, timeout: Optional[float] = None) -> Element:
        """Finds a single element with retry/timeout."""
        t_out = timeout if timeout is not None else self.timeout
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        
        while True:
            item = await self.tab.query_selector(selector)
            if item:
                return item

            if loop.time() - start_time > t_out:
                raise asyncio.TimeoutError(f"Timeout ({t_out}s) waiting for element: '{selector}'")

            await asyncio.sleep(0.5)

    async def select_all(self, selector: str, timeout: Optional[float] = None, include_frames: bool = False) -> List[Element]:
        """Finds multiple elements with retry/timeout."""
        t_out = timeout if timeout is not None else self.timeout
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        
        while True:
            items = []
            if include_frames:
                frames = await self.tab.query_selector_all("iframe")
                for fr in frames:
                    items.extend(await fr.query_selector_all(selector))
            
            items.extend(await self.tab.query_selector_all(selector))
            if items:
                return items

            if loop.time() - start_time > t_out:
                raise asyncio.TimeoutError(f"Timeout ({t_out}s) waiting for elements: '{selector}'")

            await asyncio.sleep(0.5)

    async def find(self, text: str, best_match: bool = True, timeout: Optional[float] = None) -> Element:
        """Finds element by text match."""
        t_out = timeout if timeout is not None else self.timeout
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        
        while True:
            items = await self.tab.find_elements_by_text(text)
            if items:
                if best_match and len(items) > 1:
                    # Pick closest length match
                    return min(items, key=lambda x: abs(len(x.text or "") - len(text)))
                return items[0]

            if loop.time() - start_time > t_out:
                raise asyncio.TimeoutError(f"Timeout ({t_out}s) waiting for text: '{text}'")

            await asyncio.sleep(0.5)

    async def select_text(self, selector: str, timeout: Union[int, float] = 10) -> str | None:
        """One-liner to find an element and return its inner text."""
        el = await self.select(selector, timeout=timeout)
        return el.text if el else None

    async def query_selector_all(
        self,
        selector: str,
        _node: cdp.dom.Node | Element | None = None,
    ) -> List[Element]:
        """
        equivalent of javascripts document.querySelectorAll.
        """
        doc: Any
        if not _node:
            doc = await self.send(cdp.dom.get_document(-1, True))
        else:
            doc = _node
            if getattr(doc, "node_name", "") == "IFRAME":
                 # Handle IFRAME or Element wrapping IFRAME
                 if hasattr(doc, "content_document"):
                     doc = doc.content_document
        node_ids = []

        try:
            node_ids = await self.send(
                cdp.dom.query_selector_all(doc.node_id, selector)
            )
        except ProtocolException as e:
            if _node is not None:
                if e.message is not None and "could not find node" in e.message.lower():
                    if getattr(_node, "__last", None):
                        delattr(_node, "__last")
                        return []
                    # if supplied node is not found, the dom has changed since acquiring the element
                    # therefore we need to update our passed node and try again
                    if isinstance(_node, element.Element):
                        await _node.update()
                    # make sure this isn't turned into infinite loop
                    setattr(_node, "__last", True)
                    return await self.query_selector_all(selector, _node)
            else:
                if e.message is not None and "could not find node" in e.message.lower():
                    # The document node is stale; refetch and retry once
                    doc = await self.send(cdp.dom.get_document(-1, True))
                    # Prevent double-retry by marking this node as 'last attempt'
                    setattr(doc, "__last", True)
                    return await self.query_selector_all(selector, doc)

                # assuming disable_dom_agent is available on Tab
                if hasattr(self.tab, "disable_dom_agent"):
                    await self.tab.disable_dom_agent()
                raise
        if not node_ids:
            return []
        items = []

        for nid in node_ids:
            node = util.filter_recurse(doc, lambda n: n.node_id == nid)
            # we pass along the retrieved document tree,
            # to improve performance
            if not node:
                continue
            elem = element.create(node, self.tab, doc)
            items.append(elem)

        return items

    async def query_selector(
        self,
        selector: str,
        _node: Optional[Union[cdp.dom.Node, Element]] = None,
    ) -> Element | None:
        """
        find single element based on css selector string
        """
        selector = selector.strip()

        doc: Any
        if not _node:
            doc = await self.send(cdp.dom.get_document(-1, True))
        else:
            doc = _node
            if getattr(doc, "node_name", "") == "IFRAME":
                 if hasattr(doc, "content_document"):
                     doc = doc.content_document
        node_id = None

        try:
            node_id = await self.send(cdp.dom.query_selector(doc.node_id, selector))

        except ProtocolException as e:
            if _node is not None:
                if e.message is not None and "could not find node" in e.message.lower():
                    if getattr(_node, "__last", None):
                        delattr(_node, "__last")
                        return None
                    if isinstance(_node, element.Element):
                        await _node.update()
                    setattr(_node, "__last", True)
                    return await self.query_selector(selector, _node)
            elif (
                e.message is not None
                and "could not find node" in e.message.lower()
                and doc
            ):
                doc = await self.send(cdp.dom.get_document(-1, True))
                setattr(doc, "__last", True)
                return await self.query_selector(selector, doc)
            else:
                if hasattr(self.tab, "disable_dom_agent"):
                    await self.tab.disable_dom_agent()
                raise
        if not node_id:
            return None
        node = util.filter_recurse(doc, lambda n: n.node_id == node_id)
        if not node:
            return None
        return element.create(node, self.tab, doc)

    async def resolve_node(self, backend_node_id: int) -> Element:
        """
        Resolves a backend node id into a proper Element handle.
        """
        doc = await self.send(cdp.dom.get_document(-1, True))
        try:
            # First try to find it in the current doc tree
            node = util.filter_recurse(doc, lambda n: n.backend_node_id == backend_node_id)
            if node:
                return element.create(node, self.tab, doc)
            
            # If not in tree, resolve it via CDP
            obj = await self.send(cdp.dom.resolve_node(backend_node_id=backend_node_id))
            # request_node returns nodeId
            node_id = await self.send(cdp.dom.request_node(object_id=obj.object_id))
            
            doc = await self.send(cdp.dom.get_document(-1, True))
            node = util.filter_recurse(doc, lambda n: n.node_id == node_id)
            if node:
                return element.create(node, self.tab, doc)
                
            raise ProtocolException("Could not resolve backend node into an element")
        finally:
            if hasattr(self.tab, "disable_dom_agent"):
                await self.tab.disable_dom_agent()

    async def find_elements_by_text(
        self,
        text: str,
        tag_hint: Optional[str] = None,
    ) -> list[Element]:
        """
        returns element which match the given text.
        """
        text = text.strip()
        doc = await self.send(cdp.dom.get_document(-1, True))
        search_id, nresult = await self.send(cdp.dom.perform_search(text, True))
        if nresult:
            node_ids = await self.send(
                cdp.dom.get_search_results(search_id, 0, nresult)
            )
        else:
            node_ids = []

        await self.send(cdp.dom.discard_search_results(search_id))

        if not node_ids:
            node_ids = []
        items = []
        for nid in node_ids:
            node = util.filter_recurse(doc, lambda n: n.node_id == nid)
            if not node:
                try:
                    node = await self.send(cdp.dom.resolve_node(node_id=nid))  # type: ignore
                except ProtocolException:
                    continue
                if not node:
                    continue
            try:
                elem = element.create(node, self.tab, doc)
            except Exception:
                continue
            if elem.node_type == 3:
                if not elem.parent:
                    await elem.update()

                items.append(
                    elem.parent or elem
                )
                continue
            else:
                items.append(elem)

        # iframe search logic (simplified for mixin)
        # Note: self.tab usage is correct
        iframes = util.filter_recurse_all(doc, lambda node: node.node_name == "IFRAME")
        if iframes:
            iframes_elems = [
                element.create(iframe, self.tab, iframe.content_document)
                for iframe in iframes
            ]
            for iframe_elem in iframes_elems:
                if iframe_elem.content_document:
                    iframe_text_nodes = util.filter_recurse_all(
                        iframe_elem,
                        lambda node: node.node_type == 3  # noqa
                        and text.lower() in node.node_value.lower(),
                    )
                    if iframe_text_nodes:
                        iframe_text_elems = [
                            element.create(text_node.node, self.tab, iframe_elem.tree)
                            for text_node in iframe_text_nodes
                        ]
                        items.extend(
                            text_node.parent
                            for text_node in iframe_text_elems
                            if text_node.parent
                        )
        
        if hasattr(self.tab, "disable_dom_agent"):
            await self.tab.disable_dom_agent()
        return items or []

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
