from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
import typing
from ... import cdp

if TYPE_CHECKING:
    from ..tab import Tab
    from .._contradict import ContraDict

class Position(cdp.dom.Quad):
    """helper class for element positioning"""

    def __init__(self, points: list[float]):
        super().__init__(points)
        (
            self.left,
            self.top,
            self.right,
            self.top,
            self.right,
            self.bottom,
            self.left,
            self.bottom,
        ) = points
        self.abs_x: float = 0
        self.abs_y: float = 0
        self.x = self.left
        self.y = self.top
        self.height, self.width = (self.bottom - self.top, self.right - self.left)
        self.center = (
            self.left + (self.width / 2),
            self.top + (self.height / 2),
        )

    def to_viewport(self, scale: float = 1) -> cdp.page.Viewport:
        return cdp.page.Viewport(
            x=self.x, y=self.y, width=self.width, height=self.height, scale=scale
        )

    def __repr__(self) -> str:
        return f"<Position(x={self.left}, y={self.top}, width={self.width}, height={self.height})>"

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

    @property
    def remote_object(self) -> cdp.runtime.RemoteObject | None:
        return getattr(self, '_remote_object', None)

    @property
    def object_id(self) -> cdp.runtime.RemoteObjectId | None:
        ro = self.remote_object
        return ro.object_id if ro else None
