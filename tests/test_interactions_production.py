import asyncio
import logging
import chuscraper as cs
from chuscraper.core.connection import ProtocolException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_synthetic_node_interactions():
    """
    Test that synthetic nodes (backend_node_id = -1) do not crash
    when retry_enabled=True and a ProtocolException -32000 occurs.
    """
    print("\n--- Running test_synthetic_node_interactions ---")
    config = cs.BrowserConfig(headless=True, retry_enabled=True)
    async with await cs.start(config=config) as browser:
        page = await browser.get("https://example.com")

        link = await page.select("a")
        print(f"Element: {link}, backend_node_id: {link.backend_node_id}")

        # 2. Test click() - This was the reported crash point
        await link.click()
        print("Click successful")

        # 3. Test apply()
        val = await link.apply("(el) => el.tagName")
        assert val.upper() == "A"
        print(f"Apply successful: {val}")

        # 4. Test flash()
        await link.flash(0.1)
        print("Flash successful")

        # 5. Test get_position()
        pos = await link.get_position()
        assert pos is not None
        print(f"Position: {pos}")

async def test_synthetic_node_expiration_recovery():
    """
    Specifically test that synthetic nodes can recover if their remote_object expires.
    """
    print("\n--- Running test_synthetic_node_expiration_recovery ---")
    config = cs.BrowserConfig(headless=True, retry_enabled=True)
    async with await cs.start(config=config) as browser:
        page = await browser.get("https://example.com")

        # Manually create a synthetic element for testing
        from chuscraper.core import element
        from chuscraper import cdp

        doc = await page.send(cdp.dom.get_document(-1, True))
        synthetic_node = cdp.dom.Node(
            node_id=cdp.dom.NodeId(-1),
            backend_node_id=cdp.dom.BackendNodeId(-1),
            node_type=1,
            node_name="A",
            local_name="a",
            node_value="",
            attributes=["href", "https://www.iana.org/domains/example"]
        )

        # We need a selector that works
        el = element.create(synthetic_node, page, doc, selector="a")

        # Initial re-evaluation to get a real object_id
        success = await el._re_evaluate_synthetic()
        assert success is True
        assert el.remote_object is not None

        # Now, invalidate the object_id manually to simulate expiration
        old_obj_id = el.remote_object.object_id
        el.remote_object.object_id = cdp.runtime.RemoteObjectId("invalid-id")

        # Try an interaction that uses apply() (which has retry logic)
        val = await el.apply("(el) => el.tagName")
        assert val.upper() == "A"
        assert el.remote_object.object_id != "invalid-id"
        print("Synthetic recovery successful!")

async def main():
    try:
        await test_synthetic_node_interactions()
        await test_synthetic_node_expiration_recovery()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
