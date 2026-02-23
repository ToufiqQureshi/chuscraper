from bs4 import BeautifulSoup, Tag
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from chuscraper.mobile.device import MobileDevice

class MobileElement:
    """Represents a UI element on an Android screen."""

    def __init__(self, device: 'MobileDevice', tag: Tag):
        self.device = device
        self.tag = tag

    async def click(self):
        """Clicks the center of this element."""
        # Need to parse bounds carefully.
        # Format: [x1,y1][x2,y2]
        bounds_str = self.tag.get("bounds")
        if not bounds_str:
            return

        try:
            # Example: [144,2121][304,2206]
            parts = bounds_str.replace("][", ",").replace("[", "").replace("]", "").split(",")
            x1, y1, x2, y2 = map(int, parts)

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            await self.device.tap(center_x, center_y)
        except Exception:
            pass # Fail silently if bounds are weird

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
