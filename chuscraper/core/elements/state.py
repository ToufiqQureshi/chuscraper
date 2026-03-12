from __future__ import annotations
from .base import ElementMixin
from typing import TYPE_CHECKING, Any, Optional
import typing
from ... import cdp
from .. import util
from deprecated import deprecated

if TYPE_CHECKING:
    from .._contradict import ContraDict

class ElementStateMixin(ElementMixin):
    @property
    def tag(self) -> str:
        return self.node_name.lower()

    @property
    def tag_name(self) -> str:
        return self.tag

    @property
    def node_id(self) -> cdp.dom.NodeId:
        return self.node.node_id

    @property
    def backend_node_id(self) -> cdp.dom.BackendNodeId:
        return self.node.backend_node_id

    @property
    def node_type(self) -> int:
        return self.node.node_type

    @property
    def node_name(self) -> str:
        return self.node.node_name

    @property
    def local_name(self) -> str:
        return self.node.local_name

    @property
    def node_value(self) -> str:
        return self.node.node_value

    @property
    def parent_id(self) -> cdp.dom.NodeId | None:
        return self.node.parent_id

    @property
    def child_node_count(self) -> int | None:
        return self.node.child_node_count

    @property
    def attributes(self) -> list[str] | None:
        return self.node.attributes

    @property
    def document_url(self) -> str | None:
        return self.node.document_url

    @property
    def base_url(self) -> str | None:
        return self.node.base_url

    @property
    def public_id(self) -> str | None:
        return self.node.public_id

    @property
    def system_id(self) -> str | None:
        return self.node.system_id

    @property
    def internal_subset(self) -> str | None:
        return self.node.internal_subset

    @property
    def xml_version(self) -> str | None:
        return self.node.xml_version

    @property
    def value(self) -> str | None:
        return self.node.value

    @property
    def pseudo_type(self) -> cdp.dom.PseudoType | None:
        return self.node.pseudo_type

    @property
    def pseudo_identifier(self) -> str | None:
        return self.node.pseudo_identifier

    @property
    def shadow_root_type(self) -> cdp.dom.ShadowRootType | None:
        return self.node.shadow_root_type

    @property
    def frame_id(self) -> cdp.page.FrameId | None:
        return self.node.frame_id

    @property
    def content_document(self) -> cdp.dom.Node | None:
        return self.node.content_document

    @property
    def shadow_roots(self) -> list[cdp.dom.Node] | None:
        return self.node.shadow_roots

    @property
    def template_content(self) -> cdp.dom.Node | None:
        return self.node.template_content

    @property
    def pseudo_elements(self) -> list[cdp.dom.Node] | None:
        return self.node.pseudo_elements

    @property
    def imported_document(self) -> cdp.dom.Node | None:
        return self.node.imported_document

    @property
    def distributed_nodes(self) -> list[cdp.dom.BackendNode] | None:
        return self.node.distributed_nodes

    @property
    def is_svg(self) -> bool | None:
        return self.node.is_svg

    @property
    def compatibility_mode(self) -> cdp.dom.CompatibilityMode | None:
        return self.node.compatibility_mode

    @property
    def assigned_slot(self) -> cdp.dom.BackendNode | None:
        return self.node.assigned_slot

    @deprecated(reason="Use get() instead")
    def __getattr__(self, item: str) -> str | None:
        x = getattr(self.attrs, item, None)
        if x:
            return x  # type: ignore
        return None

    def get(self, name: str) -> str | None:
        try:
            x = getattr(self.attrs, name, None)
            if x:
                return x  # type: ignore
            return None
        except AttributeError:
            return None

    def __setattr__(self, key: str, value: typing.Any) -> None:
        if key[0] != "_":
            if key[1:] not in vars(self).keys():
                self.attrs.__setattr__(key, value)
                return
        super().__setattr__(key, value)

    def __setitem__(self, key: str, value: typing.Any) -> None:
        if key[0] != "_":
            if key[1:] not in vars(self).keys():
                self.attrs[key] = value

    def __getitem__(self, item: str) -> typing.Any:
        return self.attrs.get(item, None)

    @property
    def text(self) -> str:
        text_node = util.filter_recurse(self.node, lambda n: n.node_type == 3)
        if text_node:
            return text_node.node_value
        if self.node_type == 3:
            return self.node_value
        return ""

    @property
    def text_all(self) -> str:
        text_nodes = util.filter_recurse_all(self.node, lambda n: n.node_type == 3)
        if text_nodes:
            return " ".join([n.node_value for n in text_nodes])
        if self.node_value:
             return self.node_value
        return ""

    async def to_text(self) -> str:
        """Async version of text_all that uses JS for absolute accuracy in production."""
        try:
            res = await self.apply("(el) => el.innerText || el.textContent")
            return str(res) if res else ""
        except:
            return self.text_all

    async def to_markdown(self) -> str:
        """Converts this specific element to markdown."""
        from ...extractors.markdown import html_to_markdown
        html = await self.get_html()
        return html_to_markdown(html)

    def _make_attrs(self) -> None:
        sav = None
        if self.node.attributes:
            for i, a in enumerate(self.node.attributes):
                if i == 0 or i % 2 == 0:
                    if a == "class":
                        a = "class_"
                    sav = a
                else:
                    if sav:
                        self.attrs[sav] = a
