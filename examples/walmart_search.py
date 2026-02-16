import asyncio
import os
import chuscraper as zd
import json

async def main():
    print("🚀 Starting Walmart Scraper...")
    
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
            
            # 3. Search
            query = "Sony PS5"
            
            if os.environ.get("GEMINI_API_KEY"):
                print(f"🤖 AI Pilot: Searching for '{query}'...")
                await page.ai_pilot(f"Type '{query}' in search bar and press Enter")
            else:
                print(f"⚡ No API Key. Using Standard Type & Enter for '{query}'...")
                # Walmart search input ID can vary, but let's try common ones
                # NOTE: Walmart uses shadow DOM or unique IDs often.
                # We'll use a broad selector or assuming standard input
                await page.type("input[type='search']", query)
                await page.send_keys("Enter") 
            
            # 4. Extraction
            print("👀 Extracting product info...")
            
            if os.environ.get("GEMINI_API_KEY"):
                # Walmart HTML is heavy, AI extraction is perfect for this
                products = await page.ai_extract(
                    "Extract top 3 products: title, price (current), and shipping info (e.g. '2-day shipping')."
                )
            else:
                 print("⚡ Standard Extraction...")
                 products = []
                 # Placeholder for complex Walmart selector logic
                 items = await page.query_selector_all("div[data-item-id]")
                 for item in items[:3]:
                     text = item.text
                     products.append({"raw_text": text[:100] + "..."})

            print("\n🎉 Extracted Products:\n")
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
