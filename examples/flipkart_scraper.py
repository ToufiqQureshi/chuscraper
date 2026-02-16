import asyncio
import os
import chuscraper as zd
import json

async def main():
    print("🚀 Starting Flipkart Scraper (Standard Mode)...")
    
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
            # Go directly to a category page
            url = "https://www.flipkart.com/search?q=gaming+laptops"
            print(f"🌍 Navigating to {url}...")
            page = await browser.get(url)
            
            # Handle Login Popups
            try:
                # Common close button selector for Flipkart login modal
                close_btn = "span._30XB9F, button._2KpZ6l._2doB4z" 
                if await page.query_selector(close_btn):
                    await page.click(close_btn)
                    print("✅ Closed login popup")
            except:
                pass
                
            # Extract Data
            print("👀 Extracting product listings...")
            
            # Generic product card selector (Flipkart changes these often)
            cards = await page.query_selector_all("div._1AtVbE, div._75nlfW") 
            
            data = []
            for card in cards[:5]:
                text = await card.inner_text()
                if "Laptop" in text or "Processor" in text:
                    data.append({
                        "info": text[:120].replace("\n", " ") + "..."
                    })
            
            print("\n🎉 Extracted Data (Standard):\n")
            print(json.dumps(data, indent=2))
            
            await asyncio.sleep(5)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
