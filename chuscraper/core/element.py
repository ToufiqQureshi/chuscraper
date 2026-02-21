from __future__ import annotations

import logging
import typing
from . import util
from ._contradict import ContraDict
from .. import cdp

# Import Mixins
from .elements.state import ElementStateMixin
from .elements.interaction import ElementInteractionMixin, Position
from .elements.media import ElementMediaMixin
from .elements.query import ElementQueryMixin

if typing.TYPE_CHECKING:
    from .tab import Tab

logger = logging.getLogger(__name__)


def create(
    node: cdp.dom.Node, tab: Tab, tree: typing.Optional[cdp.dom.Node] = None
) -> Element:
    """
    factory for Elements
    this is used with Tab.query_selector(_all), since we already have the tree,
    we don't need to fetch it for every single element.

    :param node: cdp dom node representation
    :param tab: the target object to which this element belongs
    :param tree: [Optional] the full node tree to which <node> belongs, enhances performance.
                when not provided, you need to call `await elem.update()` before using .children / .parent
    """

    elem = Element(node, tab, tree)

    return elem


class Element(ElementStateMixin, ElementInteractionMixin, ElementMediaMixin, ElementQueryMixin):
    def __init__(self, node: cdp.dom.Node, tab: Tab, tree: cdp.dom.Node | None = None):
        """
        Represents an (HTML) DOM Element

        :param node: cdp dom node representation
        :param tab: the target object to which this element belongs
        """
        if not node:
            raise Exception("node cannot be None")
        self._tab = tab
        self._node = node
        self._tree = tree
        self._remote_object: cdp.runtime.RemoteObject | None = None
        self._attrs = ContraDict(silent=True)
        self._make_attrs()

    @property
    def node(self) -> cdp.dom.Node:
        return self._node

    @property
    def tab(self) -> Tab:
        return self._tab

    @property
    def tree(self) -> cdp.dom.Node | None:
        return self._tree

    @tree.setter
    def tree(self, tree: cdp.dom.Node) -> None:
        self._tree = tree

    @property
    def attrs(self) -> ContraDict:
        """
        attributes are stored here, however, you can set them directly on the element object as well.
        :return:
        :rtype:
        """
        return self._attrs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Element):
            return False

        if other.backend_node_id and self.backend_node_id:
            return other.backend_node_id == self.backend_node_id

        return False

    def __repr__(self) -> str:
        tag_name = self.node.node_name.lower()
        content = ""

        # collect all text from this leaf
        if self.child_node_count:
            if self.child_node_count == 1:
                if self.children:
                    content += str(self.children[0])

            elif self.child_node_count > 1:
                if self.children:
                    for child in self.children:
                        content += str(child)

        if self.node.node_type == 3:  # we could be a text node ourselves
            content += self.node_value
            return content

        attrs = " ".join(
            [f'{k if k != "class_" else "class"}="{v}"' for k, v in self.attrs.items()]
        )
        s = f"<{tag_name} {attrs}>{content}</{tag_name}>"
        return s


async def resolve_node(tab: Tab, node_id: cdp.dom.NodeId) -> cdp.dom.Node:
    remote_obj: cdp.runtime.RemoteObject = await tab.send(
        cdp.dom.resolve_node(node_id=node_id)
    )
    if remote_obj.object_id is None:
        raise RuntimeError("could not resolve object")

    node_id = await tab.send(cdp.dom.request_node(remote_obj.object_id))
    node: cdp.dom.Node = await tab.send(cdp.dom.describe_node(node_id))
    return node
