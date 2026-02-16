import asyncio
import os
import chuscraper as zd
import json

async def main():
    print("🚀 Starting MakeMyTrip Flight Scraper...")
    
    # 1. Configure Stealth Browser (Native Chrome + Proxy is MANDATORY for MMT)
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
            print("🌍 Navigating to MakeMyTrip Flights...")
            # Direct link to a search to save time, or use homepage
            page = await browser.get("https://www.makemytrip.com/flights/")
            
            # 2. Close potential login modal
            try:
                print("⏳ Check for login modal...")
                # await page.click("span.commonModal__close", timeout=5000)
                # Using my new alias
                await page.click("span.commonModal__close", timeout=5)
                print("❌ Closed modal")
            except:
                print("✅ No modal found")
                
            # 3. Search (Hybrid)
            if os.environ.get("GEMINI_API_KEY"):
                print("🤖 AI Pilot: Searching for flights from Delhi to Mumbai...")
                await page.ai_pilot("Select 'FROM' as New Delhi and 'TO' as Mumbai. Then click Search.")
            else:
                 print("⚡ No API Key. Using Direct URL Navigation...")
                 # MMT complex forms are hard to script manually without brittle selectors.
                 # Smart fallback: Navigate to a pre-filled search URL!
                 # Date: 2 weeks from now (approx)
                 search_url = "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-20/03/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
                 await page.get(search_url)

            # 4. Extract Flight Details
            print("👀 Waiting for results and extracting...")
            
            # MMT results take time to load
            await page.wait_for_selector(".listingCard", timeout=20)
            
            if os.environ.get("GEMINI_API_KEY"):
                results = await page.ai_extract(
                    "Extract first 3 flights with: airline name, departure time, price, and duration."
                )
            else:
                print("⚡ Standard Extraction...")
                results = []
                # Placeholder selectors for MMT (these change often)
                # airline: .airlineName
                # price: .blackText
                cards = await page.query_selector_all(".listingCard")
                for card in cards[:3]:
                    text = card.text
                    results.append({"raw_text": text[:100] + "..."})
                    
            print("\n🎉 Extracted Flights:\n")
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
