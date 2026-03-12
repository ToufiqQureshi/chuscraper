import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock
import sys
import json

# Define dummy module structure
mock_modules = [
    "emoji", "browserforge", "browserforge.headers", "orjson", "websockets",
    "lxml", "lxml.html", "lxml.etree", "psutil", "msgspec", "w3lib", "w3lib.html",
    "curl_cffi", "playwright", "mss", "grapheme", "html2text", "markdownify",
    "tld", "asyncio_atexit", "cssselect", "cssselect.xpath", "cssselect.parser",
    "inflection", "loguru", "typing_extensions", "deprecated", "deprecated.sphinx"
]

for name in mock_modules:
    m = MagicMock()
    m.__spec__ = MagicMock()
    sys.modules[name] = m

import cssselect.xpath
cssselect.xpath.HTMLTranslator = type('HTMLTranslator', (object,), {})

sys.modules['chuscraper.core.stealth'] = MagicMock()
sys.modules['chuscraper.core.observability'] = MagicMock()
sys.modules['chuscraper.core.util'] = MagicMock()
sys.modules['chuscraper.core.browser'] = MagicMock()
sys.modules['chuscraper.core.tab'] = MagicMock()
sys.modules['chuscraper.core.element'] = MagicMock()
sys.modules['chuscraper.core.connection'] = MagicMock()
sys.modules['chuscraper.core._contradict'] = MagicMock()
sys.modules['chuscraper.mobile'] = MagicMock()

from chuscraper.core.tabs.dom import DomMixin
from chuscraper.cdp import dom, runtime
from chuscraper.core.connection import ProtocolException

class TestSecurityDom(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        class CombinedTab(DomMixin):
            def __init__(self):
                self._timeout = 10.0
                self._mock_send = AsyncMock()

            @property
            def tab(self):
                return self

            async def send(self, *args, **kwargs):
                return await self._mock_send(*args, **kwargs)

        self.target = CombinedTab()
        self.mock_doc = MagicMock()
        self.mock_doc.node_id = 1

    async def test_query_selector_injection_protection(self):
        async def side_effect(cmd):
            # Check cmd by name since types are generator instances or similar
            cmd_name = type(cmd).__name__
            if "get_document" in cmd_name:
                return self.mock_doc
            if "query_selector" == cmd_name:
                raise ProtocolException("Triggering fallback")
            if "evaluate" in cmd_name:
                expected_safe = json.dumps('"); alert(\'XSS\'); //')
                self.assertIn(expected_safe, cmd.expression)
                return MagicMock(value=None), None
            return MagicMock()

        self.target._mock_send.side_effect = side_effect
        await self.target.query_selector('"); alert(\'XSS\'); //')
        self.assertTrue(self.target._mock_send.called)

    async def test_query_selector_all_injection_protection(self):
        async def side_effect(cmd):
            cmd_name = type(cmd).__name__
            if "get_document" in cmd_name:
                return self.mock_doc
            if "query_selector_all" == cmd_name:
                raise ProtocolException("Triggering fallback")
            if "evaluate" in cmd_name:
                expected_safe = json.dumps('"); alert(\'XSS\'); //')
                self.assertIn(expected_safe, cmd.expression)
                return MagicMock(value=None), None
            return MagicMock()

        self.target._mock_send.side_effect = side_effect
        await self.target.query_selector_all('"); alert(\'XSS\'); //')
        self.assertTrue(self.target._mock_send.called)

if __name__ == "__main__":
    unittest.main()
