import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from chuscraper.mobile.device import MobileDevice
from chuscraper.mobile.element import MobileElement
from bs4 import BeautifulSoup
import lxml.etree as ET

@pytest.fixture
def mock_xml_dump():
    return """<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="Search" resource-id="com.agoda.mobile.consumer:id/btn_search" class="android.widget.Button" package="com.agoda.mobile.consumer" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[100,200][300,400]" />
  <node index="1" text="AED 500" resource-id="com.agoda.mobile.consumer:id/price_text" class="android.widget.TextView" package="com.agoda.mobile.consumer" content-desc="Price details" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[400,500][600,700]" />
</hierarchy>
"""

@pytest.mark.asyncio
async def test_find_element_by_text(mock_xml_dump):
    device = MobileDevice(serial="test_serial")
    device._connected = True

    with patch.object(MobileDevice, 'dump_raw_hierarchy', return_value=mock_xml_dump):
        el = await device.find_element(text="Search")
        assert el is not None
        assert el.get_text() == "Search"
        assert el.tag.get("resource-id") == "com.agoda.mobile.consumer:id/btn_search"

@pytest.mark.asyncio
async def test_find_element_by_query(mock_xml_dump):
    device = MobileDevice(serial="test_serial")
    device._connected = True

    with patch.object(MobileDevice, 'dump_raw_hierarchy', return_value=mock_xml_dump):
        # Query should match partial text
        el = await device.find_element(query="AED")
        assert el is not None
        assert "AED 500" in el.get_text()

        # Query should match partial resource-id
        el = await device.find_element(query="btn_search")
        assert el is not None
        assert el.get_text() == "Search"

@pytest.mark.asyncio
async def test_find_element_by_xpath(mock_xml_dump):
    device = MobileDevice(serial="test_serial")
    device._connected = True

    with patch.object(MobileDevice, 'dump_raw_hierarchy', return_value=mock_xml_dump):
        # XPath matching node with text containing 'AED'
        el = await device.find_element(xpath="//node[contains(@text, 'AED')]")
        assert el is not None
        assert el.get_text() == "AED 500"

        # XPath matching specific resource-id
        el = await device.find_element(xpath="//node[@resource-id='com.agoda.mobile.consumer:id/btn_search']")
        assert el is not None
        assert el.get_text() == "Search"

@pytest.mark.asyncio
async def test_mobile_element_bounds():
    tag_search = MagicMock()
    tag_search.get.side_effect = lambda attr, default=None: {
        "bounds": "[100,200][300,400]",
        "text": "Search"
    }.get(attr, default)

    device = MagicMock(spec=MobileDevice)
    el = MobileElement(device, tag_search)

    bounds = el.get_bounds()
    assert bounds == (100, 200, 300, 400)

    # Test click calculation
    el.device.tap = AsyncMock()
    await el.click()
    el.device.tap.assert_called_with(200, 300) # center of [100,200][300,400]
