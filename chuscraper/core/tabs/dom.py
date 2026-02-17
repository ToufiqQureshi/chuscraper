from __future__ import annotations
from .base import TabMixin, retry
from typing import TYPE_CHECKING, List, Optional, Union, Any
from .. import element, util
from .. import element

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

    async def query_selector_all(
        self,
        selector: str,
        _node: Optional[Union[cdp.dom.Node, Element]] = None,
    ) -> List[Element]:
        """Equivalent of JS querySelectorAll. Handles iframes and cross-frame queries."""
        doc: Any
        if not _node:
            doc = await self.send(self.cdp.dom.get_document(-1, True))
        else:
            doc = _node
            if _node.node_name == "IFRAME" and hasattr(_node, "content_document"):
                doc = _node.content_document
        
        node_ids = []
        try:
            node_ids = await self.send(self.cdp.dom.query_selector_all(doc.node_id, selector))
        except Exception as e:
            logger.debug(f"Query selector all failed: {e}")
            return []

        if not node_ids:
            return []

        from .. import util
        items = []
        for nid in node_ids:
            node = util.filter_recurse(doc, lambda n: n.node_id == nid)
            if node:
                items.append(element.create(node, self.tab, doc))
        return items

    async def find_elements_by_text(self, text: str, tag_hint: Optional[str] = None) -> List[Element]:
        """Returns elements which match the given text via CDP Search."""
        text = text.strip()
        doc = await self.send(self.cdp.dom.get_document(-1, True))
        search_id, nresult = await self.send(self.cdp.dom.perform_search(text, True))
        
        node_ids = []
        if nresult:
            node_ids = await self.send(self.cdp.dom.get_search_results(search_id, 0, nresult))
        
        await self.send(self.cdp.dom.discard_search_results(search_id))

        from .. import util
        items = []
        for nid in node_ids:
            node = util.filter_recurse(doc, lambda n: n.node_id == nid)
            if node:
                items.append(element.create(node, self.tab, doc))
        return items
