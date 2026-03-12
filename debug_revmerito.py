import asyncio
import chuscraper as zd
import logging

logging.basicConfig(level=logging.DEBUG)

async def debug_revmerito():
    print("\n--- Debugging RevMerito.com ---")
    async with await zd.start(
        headless=True,
        stealth=True,
        retry_enabled=True
    ) as browser:
        page = browser.main_tab

        # Increased timeout for complex site
        print("Navigating to revmerito.com...")
        await page.goto("https://revmerito.com")
        print(f"Loaded URL: {page.url}")

        print("Checking readyState...")
        state = await page.evaluate("document.readyState")
        print(f"ReadyState: {state}")

        print("\nDumping Content Snippet:")
        html = await page.get_content()
        print(html[:1000]) # First 1000 chars

        print("\nAttempting to select H1:")
        try:
            # The user says the text is "Maximize Your Hotel's Revenue Potential"
            # CSS Select
            h1 = await page.select("h1", timeout=10)
            print(f"CSS select found: {h1.text_all}")
        except Exception as e:
            print(f"CSS select failed: {e}")

        try:
            # XPath Select
            h1_xpath = await page.xpath("//h1")
            if h1_xpath:
                print(f"XPath found {len(h1_xpath)} elements. First text: {h1_xpath[0].text_all}")
            else:
                print("XPath found 0 elements.")
        except Exception as e:
            print(f"XPath failed: {e}")

        try:
            # Text Search
            h1_text = await page.find("Maximize Your Hotel's")
            print(f"Find by text found: {h1_text.text_all}")
        except Exception as e:
            print(f"Find by text failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_revmerito())
