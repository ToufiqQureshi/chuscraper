from bs4 import Tag
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from chuscraper.mobile.device import MobileDevice

class MobileElement:
    """Represents a UI element on an Android screen."""

    def __init__(self, device: 'MobileDevice', tag: Tag):
        self.device = device
        self.tag = tag

    async def click(self):
        """
        Clicks the center of this element.

        Raises ValueError if the element has no usable ``bounds``. This used to
        swallow every failure, so a click that silently did nothing looked
        exactly like a click that worked.
        """
        bounds_str = self.tag.get("bounds")
        if not bounds_str:
            raise ValueError(
                f"Element has no 'bounds' attribute, cannot click it: {self.tag.name}"
            )

        center_x, center_y = self._center(bounds_str)
        await self.device.tap(center_x, center_y)

    @staticmethod
    def _center(bounds_str: str) -> Tuple[int, int]:
        """Parse an android bounds string, e.g. '[144,2121][304,2206]'."""
        try:
            parts = bounds_str.replace("][", ",").replace("[", "").replace("]", "").split(",")
            x1, y1, x2, y2 = map(int, parts)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Could not parse element bounds {bounds_str!r}") from e
        return (x1 + x2) // 2, (y1 + y2) // 2

    async def type(self, text: str):
        """Clicks then types text."""
        await self.click()
        await self.device.input_text(text)

    def get_text(self) -> str:
        """Returns the text content of the element."""
        return self.tag.get("text", "") or self.tag.get("content-desc", "")

    def get_attribute(self, name: str) -> str:
        """Returns attribute value (e.g., resource-id, class)."""
        return self.tag.get(name, "")
