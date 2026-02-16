import asyncio
import os
import chuscraper as zd
import json

async def main():
    print("🚀 Starting Walmart Scraper (Standard Mode)...")
    
    # Walmart uses PerimeterX (Px), which is very strict.
    # High-quality Residential Proxy is critical here.
    proxy_url = "http://11de131690b3fdc7ba16__cr.in:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"
    
    config = zd.Config(
        browser="chrome", 
        headless=False,
        stealth=True,
        disable_webgl=True,
        proxy=proxy_url,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )

    async with await zd.start(config) as browser:
        try:
            print("🌍 Navigating to Walmart...")
            page = await browser.get("https://www.walmart.com/")
            
            # Search
            query = "Sony PS5"
            print(f"⌨️  Typing '{query}' and pressing Enter...")
            
            # Using common search selector for Walmart
            await page.wait_for_selector("input[type='search']")
            await page.fill("input[type='search']", query)
            await page.send_keys("Enter")
            
            # Wait for results
            print("⏳ Waiting for results to load...")
            await page.wait_for_selector("div[data-item-id]", timeout=15000)
            
            # Extraction
            print("👀 Extracting top products...")
            items = await page.query_selector_all("div[data-item-id]")
            
            products = []
            for item in items[:3]:
                # In standard mode, we extract available text/metadata
                text = await item.inner_text()
                products.append({
                    "preview": text[:100].replace("\n", " ") + "..."
                })

            print("\n🎉 Extracted Products (Manual):\n")
            print(json.dumps(products, indent=2))
            
            await asyncio.sleep(5)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
