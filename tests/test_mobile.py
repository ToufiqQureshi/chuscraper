import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from chuscraper.mobile import MobileDevice, MobileElement
from chuscraper.mobile.core import get_connected_devices, run_adb

class TestMobileScraper(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Read the sample dump file
        sample_path = os.path.join(os.path.dirname(__file__), "sample_data", "android_dump.xml")
        with open(sample_path, "r") as f:
            self.sample_xml = f.read()

    @patch("chuscraper.mobile.core.run_adb")
    async def test_adb_wrapper(self, mock_run_adb):
        mock_run_adb.return_value = "List of devices attached\n12345678\tdevice\n"
        devices = await get_connected_devices()
        self.assertEqual(devices, ["12345678"])
        mock_run_adb.assert_called_with(["devices"])

    @patch("chuscraper.mobile.device.MobileDevice._adb_cmd")
    async def test_find_element(self, mock_adb_cmd):
        # Mock _adb_cmd to handle file operations
        # Since dump_hierarchy pulls a file, we need to mock that process or
        # mock dump_hierarchy directly. Let's mock dump_hierarchy for cleaner testing of element finding.
        pass

    @patch("chuscraper.mobile.device.MobileDevice.dump_hierarchy")
    @patch("chuscraper.mobile.core.run_adb")
    async def test_element_interaction(self, mock_run_adb, mock_dump):
        # Setup mock dump
        from bs4 import BeautifulSoup
        mock_dump.return_value = BeautifulSoup(self.sample_xml, "xml")

        # Setup device mock connection
        mock_run_adb.return_value = "List of devices attached\n12345678\tdevice\n"

        device = MobileDevice()
        await device.connect()

        # Test find_element
        title = await device.find_element(text="Search Hotels")
        self.assertIsNotNone(title)
        self.assertEqual(title.get_text(), "Search Hotels")

        # Test find by resource-id
        input_box = await device.find_element(resource_id="com.example.app:id/search_input")
        self.assertIsNotNone(input_box)
        self.assertEqual(input_box.get_attribute("content-desc"), "Enter city")

        # Test click (should call tap)
        with patch.object(device, "tap", new_callable=AsyncMock) as mock_tap:
            await input_box.click()
            # Bounds: [100,400][980,500] -> Center: (540, 450)
            mock_tap.assert_called_with(540, 450)

        # Test type
        with patch.object(device, "input_text", new_callable=AsyncMock) as mock_input:
            with patch.object(device, "tap", new_callable=AsyncMock): # Suppress click inside type
                await input_box.type("New York")
                mock_input.assert_called_with("New York")

    @patch("chuscraper.mobile.device.MobileDevice._adb_cmd")
    async def test_device_commands(self, mock_adb_cmd):
        # Mock connection to bypass checks
        device = MobileDevice(serial="12345678")
        device._connected = True

        await device.tap(100, 200)
        mock_adb_cmd.assert_any_call("shell", "input", "tap", "100", "200")

        await device.input_text("hello world")
        mock_adb_cmd.assert_called_with("shell", "input", "text", "hello%sworld")

        await device.press_keycode(3)
        mock_adb_cmd.assert_called_with("shell", "input", "keyevent", "3")

if __name__ == "__main__":
    unittest.main()
