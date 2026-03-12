import asyncio
import chuscraper as cs
import logging
import sys

# Configure logging to see the stability fixes in action
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

async def stress_test():
    print("\n🚀 Starting Production Stress Test...")

    # Using stealth and retry_enabled for heavy sites
    async with await cs.start(
        headless=True,
        stealth=True,
        retry_enabled=True,
        browser_args=["--disable-gpu", "--no-sandbox"]
    ) as browser:
        page = browser.main_tab

        # Test Case 1: Agoda (Heavy JS, dynamic content)
        print("\n--- Testing Agoda ---")
        try:
            await page.goto("https://www.agoda.com", timeout=30)
            print(f"✅ Navigated to: {page.url}")

            # get_content
            content = await page.get_content()
            print(f"✅ get_content() length: {len(content)}")

            # select()
            search_box = await page.select("input", timeout=15)
            if search_box:
                print(f"✅ select('input') found: {search_box.node_name}")

            # xpath()
            links = await page.xpath("//a")
            print(f"✅ xpath('//a') found {len(links)} links")

            # to_markdown()
            md = await page.to_markdown(main_content_only=True)
            print(f"✅ to_markdown() snippet: {md[:100]}...")

        except Exception as e:
            print(f"❌ Agoda Test Failed: {e}")

        # Test Case 2: Amazon (Complex DOM, Anti-bot)
        print("\n--- Testing Amazon ---")
        try:
            # Using a specific product page or search to be more "heavy"
            await page.goto("https://www.amazon.com/s?k=laptop", timeout=30)
            print(f"✅ Navigated to: {page.url}")

            # find() by text
            # Amazon often has "Results" or "Price"
            results = await page.find("Results", timeout=10)
            if results:
                print(f"✅ find('Results') successful: {results.text_all[:50]}")

            # select_all()
            items = await page.select_all("div[data-component-type='s-search-result']")
            print(f"✅ select_all() found {len(items)} products")

            if items:
                # Test click on first item
                print("Testing click on first product...")
                # We use fast mode for stress testing speed
                await items[0].click(mode="fast")
                await asyncio.sleep(2)
                print(f"✅ Clicked! New URL: {page.url}")

        except Exception as e:
            print(f"❌ Amazon Test Failed: {e}")

    print("\n✨ Stress Test Completed.")

if __name__ == "__main__":
    asyncio.run(stress_test())
