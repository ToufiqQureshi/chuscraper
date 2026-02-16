import asyncio
import os
import chuscraper as zd
import json

async def main():
    print("🚀 Starting Amazon Search Scraper (No AI Mode)...")
    
    # 1. Configure Stealth Browser
    # REPLACE WITH YOUR PROXY
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
            print("🌍 Navigating to Amazon.in...")
            page = await browser.get("https://www.amazon.in/")
            
            # --- STANDARD SELECTOR APPROACH (No AI) ---
            
            # 2. Type in search bar
            search_input = "#twotabsearchtextbox"
            query = "iPhone 15 Pro Max"
            print(f"⌨️  Typing '{query}'...")
            await page.wait_for_selector(search_input)
            await page.fill(search_input, query)
            
            # 3. Click search
            print("🖱️  Clicking Search...")
            await page.click("#nav-search-submit-button")
            
            # 4. Wait for results
            await page.wait_for_selector("div.s-main-slot", state="visible")
            
            # 5. Extract Data using Standard Selectors
            print("👀 Extracting data manually...")
            # Select all product cards
            product_cards = await page.query_selector_all("div[data-component-type='s-search-result']")
            
            results = []
            for card in product_cards[:3]: # Top 3
                # Extract Title
                title_el = await card.query_selector("h2 a span")
                title = await title_el.inner_text() if title_el else "N/A"
                
                # Extract Price
                price_el = await card.query_selector(".a-price-whole")
                price = await price_el.inner_text() if price_el else "N/A"
                
                results.append({"title": title, "price": price})
            
            print("\n🎉 Extraction Complete:\n")
            print(json.dumps(results, indent=2))
            
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
