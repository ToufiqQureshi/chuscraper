import asyncio
import os
import chuscraper as zd
import json

async def main():
    print("🚀 Starting Flipkart Scraper...")
    
    # 1. Configure Stealth Browser
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
            # 2. Go directly to a category page (simulating direct access)
            url = "https://www.flipkart.com/search?q=gaming+laptops"
            print(f"🌍 Navigating to {url}...")
            page = await browser.get(url)
            
            # 3. Handle Login Popups (Common on Flipkart)
            try:
                # Simple check if a close button exists for login popup
                # Flipkart often changes this, but let's try a common one
                if await page.query_selector("button._2KpZ6l._2doB4z"): # Old selector
                    await page.click("button._2KpZ6l._2doB4z")
                    print("❌ Closed login popup")
                elif await page.query_selector("span[role='button']"): # Generic close
                    # context dependent, risky but let's try if it covers modal
                    pass 
            except:
                pass
                
            # 4. Extract Data
            print("👀 Extracting laptop deals...")
            
            if os.environ.get("GEMINI_API_KEY"):
                from chuscraper import chus_ai
                print("🤖 Using AI Extraction...")
                data = await chus_ai.extract(
                    page,
                    "Extract 5 laptops with: name, price, discount_percentage, and rating. Ignore accessories."
                )
            else:
                print("⚡ No API Key found. Using Standard Selectors...")
                # Standard Extraction Logic
                data = []
                # Flipkart uses varying classes, this is an example standard selector
                # Note: Flipkart classes like ._1AtVbE or ._75nlfW are unstable.
                # We'll use more generic attributes if possible or text search
                cards = await page.query_selector_all("div._1AtVbE") 
                # This is just a placeholder logic for standard scraping
                # Real flipkart selectors are very messy and dynamic.
                # AI is much better here. But demonstrating the fallback:
                for card in cards[:5]:
                    text = card.text
                    if "Laptop" in text:
                        data.append({"raw_text": text[:100] + "..."})
            
            print("\n🎉 Extracted Data:\n")
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
