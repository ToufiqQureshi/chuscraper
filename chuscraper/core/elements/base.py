from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
import typing

if TYPE_CHECKING:
    from ... import cdp
    from ..tab import Tab
    from .._contradict import ContraDict

class ElementMixin:
    """Base mixin for Element functionality."""
    
    @property
    def node(self) -> cdp.dom.Node:
        raise NotImplementedError

    @property
    def tab(self) -> Tab:
        raise NotImplementedError

    @property
    def tree(self) -> Optional[cdp.dom.Node]:
        raise NotImplementedError

    @property
    def attrs(self) -> ContraDict:
        raise NotImplementedError
