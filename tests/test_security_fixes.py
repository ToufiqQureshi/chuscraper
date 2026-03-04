import json
import pytest
import inspect
from unittest.mock import MagicMock, AsyncMock
from chuscraper.core.tabs.dom import DomMixin
from chuscraper.core.tabs.evaluation import EvaluationMixin
from chuscraper.cdp.runtime import RemoteObject
from chuscraper.core.connection import ProtocolException
from chuscraper import cdp

class MockTab(DomMixin, EvaluationMixin):
    def __init__(self):
        super().__init__()
        self._send = AsyncMock()
        self._timeout = 10
        self.browser = MagicMock()
        self.browser.config = MagicMock()

    async def send(self, command, *args, **kwargs):
        cmd_info = {}
        if inspect.isgenerator(command):
            try:
                cmd_info = next(command)
            except StopIteration:
                pass
        elif isinstance(command, dict):
            cmd_info = command
        elif hasattr(command, 'method'):
            cmd_info = {"method": command.method, "params": getattr(command, "params", {})}

        print(f"DEBUG: MockTab.send method={cmd_info.get('method')}")
        return await self._send(cmd_info, *args, **kwargs)

@pytest.mark.asyncio
async def test_dom_mixin_sanitization():
    tab = MockTab()

    mock_doc = cdp.dom.Node(
        node_id=cdp.dom.NodeId(1),
        backend_node_id=cdp.dom.BackendNodeId(1),
        node_type=9,
        node_name="#document",
        local_name="",
        node_value=""
    )

    tab._send.side_effect = [
        None, # enable
        mock_doc, # get_document
        ProtocolException("Fallback to JS"), # query_selector fail
        [RemoteObject(type_="object", value={"nodeType": 1}, object_id="123"), None], # evaluate fallback 1
        [RemoteObject(type_="object", object_id="123"), None], # evaluate fallback 2
    ]

    malicious_selector = "div`; alert('XSS'); `"

    try:
        await tab.query_selector(malicious_selector)
    except Exception as e:
        print(f"DEBUG: query_selector caught {e}")

    found_escaped = False
    escaped_selector = json.dumps(malicious_selector)

    for call in tab._send.call_args_list:
        args, kwargs = call
        cmd_info = args[0]
        if isinstance(cmd_info, dict) and cmd_info.get("method") == "Runtime.evaluate":
            expr = cmd_info.get("params", {}).get("expression", "")
            if escaped_selector in expr:
                found_escaped = True
                break

    assert found_escaped, f"Malicious selector {escaped_selector} was not found in any Runtime.evaluate call"

@pytest.mark.asyncio
async def test_evaluation_mixin_unchanged():
    tab = MockTab()

    # In EvaluationMixin, js_dumps uses obj_name as a reference, not a string literal.
    # We verify that it is NOT escaped by json.dumps if we revert the fix there.
    obj_ref = "window.location"
    tab._send.return_value = [RemoteObject(type_="object", value={"foo": "bar"}), None]

    await tab.js_dumps(obj_ref)

    found_reference = False
    for call in tab._send.call_args_list:
        args, kwargs = call
        cmd_info = args[0]
        if isinstance(cmd_info, dict) and cmd_info.get("method") == "Runtime.evaluate":
            expr = cmd_info.get("params", {}).get("expression", "")
            if obj_ref in expr and json.dumps(obj_ref) not in expr:
                found_reference = True
                break

    assert found_reference, "Object reference was escaped (incorrect for js_dumps) or not found"
