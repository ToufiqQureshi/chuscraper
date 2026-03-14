import asyncio
import chuscraper as cs
import logging
import pathlib

logging.basicConfig(level=logging.INFO)

async def verify_17_fixes():
    print("\n🚀 Verifying 17 Production Bug Fixes...")

    async with await cs.start(headless=True) as browser:
        # 1. Browser.scrape helper
        print("Testing Browser.scrape()...")
        try:
            await browser.get("https://example.com")
            h1 = await browser.scrape("h1")
            print(f"✅ Browser.scrape found: {h1.text_all}")
        except Exception as e: print(f"❌ Browser.scrape failed: {e}")

        tab = browser.main_tab

        # 2. Storage Mixin: set_cookie
        print("Testing set_cookie signature...")
        try:
            await tab.set_cookie("test_cookie", "test_value")
            print("✅ set_cookie successful")
        except Exception as e: print(f"❌ set_cookie failed: {e}")

        # 3. Storage Mixin: local_storage
        print("Testing local_storage API...")
        try:
            await tab.set_local_storage("mykey", "myval")
            val = await tab.get_local_storage("mykey")
            print(f"✅ local_storage: {val}")
            assert val == "myval"
        except Exception as e: print(f"❌ local_storage failed: {e}")

        # 4. Tab.print_to_pdf bytes
        print("Testing print_to_pdf bytes...")
        try:
            pdf_bytes = await tab.print_to_pdf()
            print(f"✅ print_to_pdf returned {len(pdf_bytes)} bytes")
            assert isinstance(pdf_bytes, bytes)
        except Exception as e: print(f"❌ print_to_pdf failed: {e}")

        # 5. Interaction: hover
        print("Testing hover()...")
        try:
            await tab.hover("a")
            print("✅ hover successful")
        except Exception as e: print(f"❌ hover failed: {e}")

        # 6. Interaction: type
        print("Testing type()...")
        try:
            # We need an input, let's use a dummy one if needed or just call it
            # Since example.com has no input, we'll navigate to a site that does or inject one
            await tab.evaluate("document.body.innerHTML += '<input id=test_input>'")
            await tab.type("#test_input", "hello world")
            val = await tab.evaluate("document.getElementById('test_input').value")
            print(f"✅ type result: {val}")
            assert val == "hello world"
        except Exception as e: print(f"❌ type failed: {e}")

        # 7. Metrics fallback
        print("Testing performance metrics...")
        try:
            metrics = await tab.get_performance_metrics()
            print(f"✅ Metrics found: {len(metrics)}")
        except Exception as e: print(f"❌ Metrics failed: {e}")

        # 8. Overlay fallback
        print("Testing highlight_overlay...")
        try:
            h1 = await tab.select("h1")
            await h1.highlight_overlay()
            print("✅ highlight_overlay successful")
        except Exception as e: print(f"❌ highlight_overlay failed: {e}")

        # 9. Extra headers
        print("Testing set_extra_headers...")
        try:
            await tab.set_extra_headers({"X-Test": "Value"})
            print("✅ set_extra_headers successful")
        except Exception as e: print(f"❌ set_extra_headers failed: {e}")

        # 10. Multi-tab: Browser.get(new_tab=True)
        print("Testing new_tab...")
        try:
            new_tab = await browser.get("https://example.com", new_tab=True)
            print(f"✅ new_tab created: {new_tab.target_id}")
            # 11. Tab.close() CancelledError fix
            await new_tab.close()
            print("✅ Tab.close() successful")
        except Exception as e: print(f"❌ new_tab/close failed: {e}")

        # 12. Browser.targets property
        print("Testing browser.targets...")
        try:
            print(f"✅ Targets: {len(browser.targets)}")
        except Exception as e: print(f"❌ browser.targets failed: {e}")

        # 13. Browser.grant_all_permissions
        print("Testing grant_all_permissions...")
        try:
            await browser.grant_all_permissions("https://example.com")
            print("✅ grant_all_permissions successful")
        except Exception as e: print(f"❌ grant_all_permissions failed: {e}")

        # 14. Element sub-selection
        print("Testing element sub-selection...")
        try:
            await tab.goto("https://example.com")
            body = await tab.select("body")
            h1 = await body.select_one("h1")
            print(f"✅ Sub-selection found: {h1.text_all}")
        except Exception as e: print(f"❌ sub-selection failed: {e}")

        # 15. Window state (fullscreen)
        print("Testing fullscreen...")
        try:
            await tab.fullscreen()
            print("✅ fullscreen successful")
            await tab.medimize() # normal
            print("✅ medimize successful")
        except Exception as e: print(f"❌ window state failed: {e}")

        # 16. tile_windows
        print("Testing tile_windows...")
        try:
            await browser.tile_windows()
            print("✅ tile_windows successful")
        except Exception as e: print(f"❌ tile_windows failed: {e}")

    print("\n✨ Verification Completed.")

if __name__ == "__main__":
    asyncio.run(verify_17_fixes())
