import asyncio
import os
import time
from typing import List, Optional, Tuple, Dict
from chuscraper.mobile.core import run_adb
from chuscraper.mobile.element import MobileElement
from bs4 import BeautifulSoup

class MobileDevice:
    """Controls a connected Android device via ADB."""

    def __init__(self, serial: Optional[str] = None):
        self.serial = serial
        self._connected = False

    async def connect(self):
        """Establishes connection to the device."""
        from chuscraper.mobile.core import get_connected_devices

        devices = await get_connected_devices()
        if not devices:
            raise RuntimeError("No Android devices connected.")

        if self.serial and self.serial not in devices:
            raise RuntimeError(f"Device {self.serial} not found.")

        if not self.serial:
            self.serial = devices[0]

        self._connected = True
        return self

    async def _adb_cmd(self, *args, timeout: float = 10.0) -> str:
        """Runs an ADB command for this specific device."""
        if not self._connected:
            await self.connect()

        cmd = ["-s", self.serial] + list(args)
        return await run_adb(cmd, timeout=timeout)

    async def dump_hierarchy(self) -> BeautifulSoup:
        """Dumps the current UI hierarchy and returns a BeautifulSoup object."""
        # Dump to device temp file
        # Note: 'uiautomator dump' creates /sdcard/window_dump.xml by default on older androids
        # but modern ones respect the path. Some devices fail if path isn't sdcard.
        # Safest is /sdcard/window_dump.xml

        remote_path = "/sdcard/window_dump.xml"
        await self._adb_cmd("shell", "uiautomator", "dump", remote_path)

        # Pull to host temp file
        temp_local = f"dump_{int(time.time())}.xml"
        await self._adb_cmd("pull", remote_path, temp_local)

        try:
            if not os.path.exists(temp_local):
                # Fallback: sometimes dump fails silently or to a different path
                return BeautifulSoup("<hierarchy></hierarchy>", "xml")

            with open(temp_local, "r", encoding="utf-8", errors="ignore") as f:
                xml_content = f.read()
            soup = BeautifulSoup(xml_content, "xml")
            return soup
        finally:
            if os.path.exists(temp_local):
                os.remove(temp_local)

    async def find_element(self, **kwargs) -> Optional[MobileElement]:
        """Finds a single element matching criteria."""
        soup = await self.dump_hierarchy()

        # Handle 'resource_id' to 'resource-id' conversion and 'class_name' to 'class'
        if "resource_id" in kwargs:
            kwargs["resource-id"] = kwargs.pop("resource_id")
        if "class_name" in kwargs:
            kwargs["class"] = kwargs.pop("class_name")

        tag = soup.find(attrs=kwargs) if kwargs else None
        if tag:
            return MobileElement(self, tag)
        return None

    async def find_elements(self, **kwargs) -> List[MobileElement]:
        """Finds all elements matching criteria."""
        soup = await self.dump_hierarchy()

        # Handle 'resource_id' to 'resource-id' conversion and 'class_name' to 'class'
        if "resource_id" in kwargs:
            kwargs["resource-id"] = kwargs.pop("resource_id")
        if "class_name" in kwargs:
            kwargs["class"] = kwargs.pop("class_name")

        tags = soup.find_all(attrs=kwargs) if kwargs else []
        return [MobileElement(self, tag) for tag in tags]

    async def tap(self, x: int, y: int):
        """Taps at specific coordinates."""
        await self._adb_cmd("shell", "input", "tap", str(x), str(y))

    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500):
        """Swipes from (x1, y1) to (x2, y2)."""
        await self._adb_cmd("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration))

    async def input_text(self, text: str):
        """Types text (must be focused first). Replaces spaces with %s."""
        escaped_text = text.replace(" ", "%s")
        await self._adb_cmd("shell", "input", "text", escaped_text)

    async def press_keycode(self, code: int):
        """Presses a hardware key (e.g., 3 for HOME, 4 for BACK)."""
        await self._adb_cmd("shell", "input", "keyevent", str(code))

    async def screenshot(self, filename: str):
        """Takes a screenshot and saves it to local file."""
        remote_path = "/sdcard/screen.png"
        await self._adb_cmd("shell", "screencap", "-p", remote_path)
        await self._adb_cmd("pull", remote_path, filename)
        await self._adb_cmd("shell", "rm", remote_path)
