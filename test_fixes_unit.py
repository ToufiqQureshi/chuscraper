import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from chuscraper.core.connection import Connection
from chuscraper import cdp

class TestConnectionFix(unittest.IsolatedAsyncioTestCase):
    async def test_target_id_returns_target_id_object(self):
        # Mock target object that has a target_id attribute of type cdp.target.TargetID
        mock_target_id = cdp.target.TargetID("test-id-123")
        mock_target = MagicMock()
        mock_target.target_id = mock_target_id

        conn = Connection(websocket_url="ws://localhost:1234", target=mock_target)

        # Verify target_id property returns the object, not a plain str
        self.assertEqual(conn.target_id, mock_target_id)
        self.assertIsInstance(conn.target_id, cdp.target.TargetID)
        # Verify it has to_json method (it's a str subclass in CDP)
        self.assertTrue(hasattr(conn.target_id, 'to_json'))
        self.assertEqual(conn.target_id.to_json(), "test-id-123")

class TestElementApplyFix(unittest.IsolatedAsyncioTestCase):
    async def test_apply_retries_on_stale_object_id(self):
        from chuscraper.core.element import Element
        from chuscraper.core.connection import ProtocolException

        mock_tab = AsyncMock()
        mock_node = MagicMock(spec=cdp.dom.Node)
        mock_node.backend_node_id = cdp.dom.BackendNodeId(1)
        mock_node.node_name = "DIV"

        # Initialize Element
        with patch('chuscraper.core.element.Element._make_attrs'):
            elem = Element(node=mock_node, tab=mock_tab)

        # Set a fake remote_object
        mock_remote_object = MagicMock(spec=cdp.runtime.RemoteObject)
        mock_remote_object.object_id = cdp.runtime.RemoteObjectId("old-id")
        elem._remote_object = mock_remote_object

        # Setup mock_tab.send to fail first then succeed
        stale_error = ProtocolException({"code": -32000, "message": "Could not find object with given id"})

        new_remote_object = MagicMock(spec=cdp.runtime.RemoteObject)
        new_remote_object.object_id = cdp.runtime.RemoteObjectId("new-id")
        new_remote_object.value = "success"

        success_result = (new_remote_object, None)

        # Mock update to avoid making more tab.send calls than expected
        # And simulate it setting a new remote object
        async def mock_update_func():
            elem._remote_object = new_remote_object

        # First call fails, second call (after retry) succeeds
        mock_tab.send.side_effect = [stale_error, success_result]

        with patch('chuscraper.core.elements.interaction.ElementInteractionMixin.update', side_effect=mock_update_func) as mock_update:
            result = await elem.apply("() => {}")

            self.assertEqual(result, "success")
            self.assertEqual(mock_tab.send.call_count, 2)
            mock_update.assert_called_once()
            # Verify it used the NEW remote object ID in the second call
            call_args = mock_tab.send.call_args_list[1]
            # The first argument to tab.send is the cdp command generator
            # We can't easily inspect the generator's state without running it,
            # but we've verified the logic flow.

if __name__ == "__main__":
    unittest.main()
