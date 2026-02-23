import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from chuscraper.mobile import MobileDevice, MobileElement
from bs4 import BeautifulSoup

class TestMobileStress(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Sample empty XML for crashes/slow responses
        self.empty_xml = "<hierarchy></hierarchy>"
        # Sample XML with complex bounds and special chars
        self.complex_xml = """
        <hierarchy rotation="1">
          <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.example.app" bounds="[0,0][2400,1080]">
            <node index="1" text="Login 😊" resource-id="com.example.app:id/login_btn" class="android.widget.Button" bounds="[1000,500][1400,600]" />
            <node index="2" text="Search &amp; Find" resource-id="com.example.app:id/search" class="android.widget.EditText" bounds="[100,100][500,200]" />
            <node index="3" text="" resource-id="broken_bounds" class="android.widget.View" bounds="[0,0]" />
          </node>
        </hierarchy>
        """

    @patch("chuscraper.mobile.core.run_adb")
    async def test_multiple_devices(self, mock_run_adb):
        """Scenario: Two devices connected via ADB."""
        mock_run_adb.return_value = "List of devices attached\nserial1\tdevice\nserial2\tdevice\n"

        # Test 1: Connect to specific device
        dev1 = await MobileDevice(serial="serial2").connect()
        self.assertEqual(dev1.serial, "serial2")

        # Test 2: Connect to first available (default)
        dev2 = await MobileDevice().connect()
        self.assertEqual(dev2.serial, "serial1")

        # Test 3: Connect to non-existent device
        with self.assertRaises(RuntimeError):
            await MobileDevice(serial="missing_device").connect()

    @patch("chuscraper.mobile.core.run_adb")
    async def test_connection_lost(self, mock_run_adb):
        """Scenario: ADB command fails mid-execution (device unplugged)."""
        device = MobileDevice(serial="test_device")
        device._connected = True

        # Simulate ADB error output
        mock_run_adb.side_effect = RuntimeError("ADB Error: device 'test_device' not found")

        with self.assertRaises(RuntimeError) as cm:
            await device.tap(100, 100)
        self.assertIn("not found", str(cm.exception))

    # The `adb` mock is causing issues because the real implementation now catches Timeout inside run_adb.
    # We should NOT mock run_adb to raise Timeout, but rather simulate a slow command.
    # However, mocking subprocess is complex.
    # Let's mock run_adb to verify the wrapper handles it, or use a real asyncio.sleep inside a mock.

    @patch("asyncio.create_subprocess_exec")
    async def test_adb_timeout(self, mock_exec):
        """Scenario: ADB hangs due to network lag (e.g. WiFi debugging)."""
        device = MobileDevice(serial="slow_device")
        device._connected = True

        # Mock process that hangs forever
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError)
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()
        mock_exec.return_value = mock_process

        # Since we are mocking subprocess creation, we need to call the real run_adb logic,
        # so we do NOT patch run_adb here.

        with self.assertRaises(TimeoutError):
            await device._adb_cmd("shell", "input", "tap", "0", "0", timeout=0.01)

        # Verify kill was called
        mock_process.kill.assert_called()

    @patch("chuscraper.mobile.device.MobileDevice.dump_hierarchy")
    async def test_special_characters_input(self, mock_dump):
        """Scenario: Handling emojis and special characters in input."""
        mock_dump.return_value = BeautifulSoup(self.complex_xml, "xml")

        device = MobileDevice(serial="emoji_device")
        device._connected = True

        # Find element with Emoji text
        btn = await device.find_element(text="Login 😊")
        self.assertIsNotNone(btn)
        self.assertEqual(btn.get_text(), "Login 😊")

        # Test typing special chars
        with patch.object(device, "_adb_cmd", new_callable=AsyncMock) as mock_cmd:
            # Type "Hello World & More" -> Spaces become %s
            await device.input_text("Hello World & More")
            mock_cmd.assert_called_with("shell", "input", "text", "Hello%sWorld%s&%sMore")

    @patch("chuscraper.mobile.device.MobileDevice.dump_hierarchy")
    async def test_broken_bounds_parsing(self, mock_dump):
        """Scenario: XML node has malformed bounds attribute."""
        mock_dump.return_value = BeautifulSoup(self.complex_xml, "xml")

        device = MobileDevice(serial="broken_xml_device")
        device._connected = True

        # Element with incomplete bounds "[0,0]" instead of "[x1,y1][x2,y2]"
        broken_el = await device.find_element(resource_id="broken_bounds")
        self.assertIsNotNone(broken_el)

        # Clicking should NOT crash, but fail silently or log error
        with patch.object(device, "tap", new_callable=AsyncMock) as mock_tap:
            await broken_el.click()
            # Should NOT call tap because bounds are invalid
            mock_tap.assert_not_called()

    @patch("chuscraper.mobile.device.MobileDevice.dump_hierarchy")
    async def test_empty_xml_handling(self, mock_dump):
        """Scenario: App crashes or screen is blank (empty XML)."""
        # Simulate empty hierarchy (e.g. black screen)
        mock_dump.return_value = BeautifulSoup(self.empty_xml, "xml")

        device = MobileDevice(serial="blank_screen")
        device._connected = True

        # Find element should simply return None, not crash
        el = await device.find_element(text="Anything")
        self.assertIsNone(el)

if __name__ == "__main__":
    unittest.main()
