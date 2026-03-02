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

    async def test_apply_retries_on_stale_object_id(self):
        from chuscraper.core.connection import ProtocolException

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
            stale_error,        # 1. apply() call fails
            None,               # 2. update() -> cdp.dom.enable()
            mock_doc,           # 3. update() -> cdp.dom.get_document()
            new_remote_object,  # 4. update() -> cdp.dom.resolve_node()
            success_result      # 5. retry apply() call succeeds
        ]

        with patch('chuscraper.core.util.filter_recurse', return_value=self.mock_node):
            result = await self.elem.apply("() => {}")
            self.assertEqual(result, "success")
            self.assertEqual(self.mock_tab.send.call_count, 5)

    async def test_click_uses_apply_and_retries(self):
        from chuscraper.core.connection import ProtocolException

        # Mock flash on the Element class to affect all instances
        from chuscraper.core.elements.media import ElementMediaMixin
        with patch.object(ElementMediaMixin, 'flash', new_callable=AsyncMock):
            old_remote_object = MagicMock(spec=cdp.runtime.RemoteObject)
            old_remote_object.object_id = cdp.runtime.RemoteObjectId("old-click-id")
            self.elem._remote_object = old_remote_object

            stale_error = ProtocolException({"code": -32000, "message": "Could not find object with given id"})
            new_remote_object = MagicMock(spec=cdp.runtime.RemoteObject)
            new_remote_object.object_id = cdp.runtime.RemoteObjectId("new-click-id")
            new_remote_object.value = None
            success_result = (new_remote_object, "something")
            mock_doc = MagicMock(spec=cdp.dom.Node)

            self.mock_tab.send.side_effect = [
                stale_error,        # 1. apply() via click() fails
                None,               # 2. update() -> cdp.dom.enable()
                mock_doc,           # 3. update() -> cdp.dom.get_document()
                new_remote_object,  # 4. update() -> cdp.dom.resolve_node()
                success_result      # 5. retry apply() succeeds
            ]

            with patch('chuscraper.core.util.filter_recurse', return_value=self.mock_node):
                await self.elem.click(mode='cdp')
                self.assertEqual(self.mock_tab.send.call_count, 5)

if __name__ == "__main__":
    unittest.main()
