import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from chuscraper.mobile.device import MobileDevice
from chuscraper.mobile.element import MobileElement
from bs4 import BeautifulSoup

@pytest.fixture
def mock_xml_dump():
    return """<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="Search" clickable="true" resource-id="id1" class="android.widget.Button" bounds="[0,0][100,100]" />
  <node index="1" text="Search" clickable="true" resource-id="id2" class="android.widget.Button" bounds="[100,0][200,100]" />
  <node index="2" text="AED 500" clickable="false" resource-id="price" class="android.widget.TextView" bounds="[0,100][200,200]" />
</hierarchy>
"""

@pytest.mark.asyncio
async def test_xpath_indexing(mock_xml_dump):
    device = MobileDevice(serial="test_serial")
    device._connected = True

    with patch.object(MobileDevice, 'dump_raw_hierarchy', return_value=mock_xml_dump):
        # Find first 'Search' button
        el1 = await device.find_element(xpath="(//node[@text='Search'])[1]")
        assert el1 is not None
        assert el1.tag.get("resource-id") == "id1"

        # Find second 'Search' button
        el2 = await device.find_element(xpath="(//node[@text='Search'])[2]")
        assert el2 is not None
        assert el2.tag.get("resource-id") == "id2"

@pytest.mark.asyncio
async def test_get_clickable_elements(mock_xml_dump):
    device = MobileDevice(serial="test_serial")
    device._connected = True

    with patch.object(MobileDevice, 'dump_raw_hierarchy', return_value=mock_xml_dump):
        clickables = await device.get_clickable_elements()
        assert len(clickables) == 2 # Only 'Search' buttons are clickable
        assert clickables[0]["text"] == "Search"
        assert clickables[0]["xpath"] == "(//node[@clickable='true'])[1]"
        assert clickables[1]["text"] == "Search"
        assert clickables[1]["xpath"] == "(//node[@clickable='true'])[2]"
