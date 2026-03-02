import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from chuscraper.core.connection import Connection
from chuscraper import cdp

class TestConnectionFix(unittest.IsolatedAsyncioTestCase):
    async def test_target_id_returns_target_id_object(self):
        mock_target_id = cdp.target.TargetID("test-id-123")
        mock_target = MagicMock()
        mock_target.target_id = mock_target_id
        conn = Connection(websocket_url="ws://localhost:1234", target=mock_target)
        self.assertEqual(conn.target_id, mock_target_id)
        self.assertIsInstance(conn.target_id, cdp.target.TargetID)

class TestElementInteractionFixes(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from chuscraper.core.element import Element
        self.mock_tab = AsyncMock()
        self.mock_node = MagicMock(spec=cdp.dom.Node)
        self.mock_node.backend_node_id = cdp.dom.BackendNodeId(1)
        self.mock_node.node_name = "DIV"
        self.mock_node.attributes = []

        with patch('chuscraper.core.element.Element._make_attrs'):
            self.elem = Element(node=self.mock_node, tab=self.mock_tab)

    async def test_fill_does_not_click_automatically(self):
        from chuscraper.core.elements.interaction import ElementInteractionMixin

        # Patching on the class because instance attribute patching failed
        with patch.object(ElementInteractionMixin, 'click', new_callable=AsyncMock) as mock_click, \
             patch.object(ElementInteractionMixin, 'clear_input', new_callable=AsyncMock) as mock_clear, \
             patch.object(ElementInteractionMixin, 'send_keys', new_callable=AsyncMock) as mock_send_keys:

            await self.elem.fill("test")
            mock_click.assert_not_called()
            mock_clear.assert_called_once()
            mock_send_keys.assert_called_once_with("test")

    async def test_apply_no_retry_by_default(self):
        from chuscraper.core.connection import ProtocolException

        stale_error = ProtocolException({"code": -32000, "message": "Could not find object with given id"})
        self.mock_tab.send.side_effect = [stale_error]

        with self.assertRaises(ProtocolException):
            await self.elem.apply("() => {}")

        self.assertEqual(self.mock_tab.send.call_count, 1)

    async def test_apply_retry_when_explicit(self):
        from chuscraper.core.connection import ProtocolException
        from chuscraper.core.elements.interaction import ElementInteractionMixin

        # Set initial remote object so it doesn't try to resolve it first
        old_remote_object = MagicMock(spec=cdp.runtime.RemoteObject)
        old_remote_object.object_id = cdp.runtime.RemoteObjectId("old-id")
        self.elem._remote_object = old_remote_object

        stale_error = ProtocolException({"code": -32000, "message": "Could not find object with given id"})
        new_remote_object = MagicMock(spec=cdp.runtime.RemoteObject)
        new_remote_object.object_id = cdp.runtime.RemoteObjectId("new-id")
        new_remote_object.value = "success"
        success_result = (new_remote_object, "something")
        mock_doc = MagicMock(spec=cdp.dom.Node)

        self.mock_tab.send.side_effect = [
            stale_error,        # 1. First send() call in apply() fails
            None,               # 2. update() -> enable
            mock_doc,           # 3. update() -> getDocument
            new_remote_object,  # 4. update() -> resolveNode
            success_result      # 5. retry apply() succeeds
        ]

        with patch('chuscraper.core.util.filter_recurse', return_value=self.mock_node), \
             patch.object(ElementInteractionMixin, 'update', wraps=self.elem.update) as mock_update:
            result = await self.elem.apply("() => {}", retry=True)
            self.assertEqual(result, "success")
            self.assertEqual(self.mock_tab.send.call_count, 5)
            mock_update.assert_called_once()

if __name__ == "__main__":
    unittest.main()
