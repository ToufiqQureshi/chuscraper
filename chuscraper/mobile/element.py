from bs4 import Tag
from typing import TYPE_CHECKING, Optional, Tuple
import re

if TYPE_CHECKING:
    from chuscraper.mobile.device import MobileDevice

class MobileElement:
    """Represents a UI element on an Android screen."""

    def __init__(self, device: 'MobileDevice', tag: Tag):
        self.device = device
        self.tag = tag

    def get_bounds(self) -> Optional[Tuple[int, int, int, int]]:
        """Parses the 'bounds' attribute into (x1, y1, x2, y2)."""
        bounds_str = self.tag.get("bounds")
        if not bounds_str:
            return None

        try:
            # Example: [144,2121][304,2206]
            match = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
            if len(match) == 2:
                x1, y1 = map(int, match[0])
                x2, y2 = map(int, match[1])
                return (x1, y1, x2, y2)
        except Exception:
            return None
        return None

    async def click(self):
        """Clicks the center of this element."""
        bounds = self.get_bounds()
        if not bounds:
            raise RuntimeError(f"Could not determine bounds for element: {self.tag.name}")

        x1, y1, x2, y2 = bounds
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        await self.device.tap(center_x, center_y)

    async def type(self, text: str, clear: bool = False):
        """Clicks then types text."""
        await self.click()
        if clear:
            # Basic clear logic: move to end and backspace
            # 123 is KEYCODE_MOVE_END, 67 is KEYCODE_DEL
            await self.device.press_keycode(123)
            for _ in range(30): # Backspace 30 times as a safe guess
                await self.device.press_keycode(67)

        await self.device.input_text(text)

    def get_text(self) -> str:
        """Returns the text content of the element."""
        return self.tag.get("text", "") or self.tag.get("content-desc", "")

    def get_attribute(self, name: str) -> str:
        """Returns attribute value (e.g., resource-id, class)."""
        return self.tag.get(name, "")

    def __repr__(self):
        return f"<MobileElement {self.tag.name} text='{self.get_text()}' bounds='{self.tag.get('bounds')}'>"
