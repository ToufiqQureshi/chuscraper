from __future__ import annotations
from .base import ElementMixin
from typing import TYPE_CHECKING, List, Optional
from ... import cdp
from .. import util
import typing
from chuscraper.engine.parser import Selector as ChuSelector
from chuscraper.engine.core.extract import Convertor

if TYPE_CHECKING:
    from ..element import Element

def element_create_helper(node: cdp.dom.Node, tab: Any, tree: Optional[cdp.dom.Node] = None) -> Element:
    # We need to import Element inside the function or rely on a passed factory check
    # But Element is defined in ..element.py
    # To avoid circular imports at module level, we import locally
    from ..element import create
    return create(node, tab, tree)

class ElementQueryMixin(ElementMixin):
    async def query_selector_all(self, selector: str) -> list[Element]:
        """
        like js querySelectorAll()
        """
        # self.update() call is in Element.query_selector_all, we should keep it?
        # In Element.py: await self.update(); return await self.tab.query_selector_all...
        # We need to define update() in a mixin or abstract base
        # It's in InteractionMixin usually or Base.
        # Let's assume update() is available via interface
        if hasattr(self, 'update'):
            await self.update() # type: ignore
        return await self.tab.query_selector_all(selector, _node=self) # type: ignore

    async def query_selector(self, selector: str) -> Element | None:
        """
        like js querySelector()
        """
        if hasattr(self, 'update'):
            await self.update() # type: ignore
        return await self.tab.query_selector(selector, self) # type: ignore

    async def select_all(self, selector: str, adaptive: bool = False, identifier: str = "", auto_save: bool = True, percentage: int = 0) -> List[Element]:
        """
        Uses Chuscraper's advanced Selector engine to find child elements.
        """
        # Get outer HTML of this element
        html = await self.tab.send(cdp.dom.get_outer_html(node_id=self.node.node_id))
        # Create adaptive selector for this sub-tree
        scr_sel = ChuSelector(html, url=self.tab.url, adaptive=adaptive)
        # Find elements
        results = scr_sel.css(selector, identifier=identifier, adaptive=adaptive, auto_save=auto_save, percentage=percentage)
        
        elements = []
        for res in results:
            xpath = res.generate_xpath_selector
            # Query relative to this element
            found = await self.tab.query_selector_all(f"xpath:{xpath}", _node=self)
            if found:
                elements.extend(found)
        return elements

    async def select_one(self, selector: str, adaptive: bool = False, identifier: str = "", auto_save: bool = True, percentage: int = 0) -> Optional[Element]:
        """Finds a single child element using Chuscraper's engine."""
        res = await self.select_all(selector, adaptive, identifier, auto_save, percentage)
        return res[0] if res else None

    async def _get_safe_outer_html(self) -> str:
        """Helper to safely extract HTML even if NodeId drops from DevTools Agent tree"""
        try:
            return await self.tab.send(cdp.dom.get_outer_html(node_id=self.node.node_id))
        except Exception:
            # Fallback 1: Absolute worst-case scenario: we construct the HTML manually from our cached Element state
            # since DevTools drops the active node mapping instantly after finding it on dynamic sites
            node_name = self.node.node_name.lower()
            if node_name == "#text":
                return self.node.node_value or ""
                
            attrs_str = ""
            if hasattr(self.node, 'attributes') and self.node.attributes:
                attrs = dict(zip(self.node.attributes[0::2], self.node.attributes[1::2]))
                for k, v in attrs.items():
                    attrs_str += f' {k}="{v}"'
            
            # Since to_text/to_markdown are used for content extraction, giving it a synthetic wrapper
            # allows our Parsers to succeed even if we lost the live DOM connection.
            return f"<{node_name}{attrs_str}>{self.node.node_value or ''}</{node_name}>"

    async def to_markdown(self) -> str:
        """Converts this element to Markdown."""
        html = await self._get_safe_outer_html()
        if not html: return ""
        sel = ChuSelector(html, url=self.tab.url)
        content_gen = Convertor._extract_content(sel, extraction_type="markdown")
        return "".join(content_gen)

    async def to_text(self) -> str:
        """Converts this element to plain text."""
        html = await self._get_safe_outer_html()
        if not html: return ""
        sel = ChuSelector(html, url=self.tab.url)
        content_gen = Convertor._extract_content(sel, extraction_type="text")
        return "".join(content_gen)

    @property
    def parent(self) -> typing.Union[Element, None]:
        """
        get the parent element (node) of current element(node)
        :return:
        :rtype:
        """
        if not self.tree:
            raise RuntimeError("could not get parent since the element has no tree set")
        parent_node = util.filter_recurse(
            self.tree, lambda n: n.node_id == self.node.parent_id
        )
        if not parent_node:
            return None
        return element_create_helper(parent_node, tab=self.tab, tree=self.tree)

    @property
    def children(self) -> list[Element]:
        """
        returns the elements' children. those children also have a children property
        so you can browse through the entire tree as well.
        :return:
        :rtype:
        """
        _children = []
        if self.node.node_name == "IFRAME":
            # iframes are not exact the same as other nodes
            # the children of iframes are found under
            # the .content_document property, which is of more
            # use than the node itself
            frame = self.node.content_document
            if not frame or not frame.children or not frame.child_node_count:
                return []
            for child in frame.children:
                child_elem = element_create_helper(child, self.tab, frame)
                if child_elem:
                    _children.append(child_elem)
            # self._node = frame
            return _children
        elif not self.node.child_node_count:
            return []
        if self.node.children:
            for child in self.node.children:
                child_elem = element_create_helper(child, self.tab, self.tree)
                if child_elem:
                    _children.append(child_elem)
        return _children
