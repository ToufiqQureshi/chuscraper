from __future__ import annotations
from .base import ElementMixin
from typing import TYPE_CHECKING, List, Optional
from ... import cdp
from .. import util
import typing

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
