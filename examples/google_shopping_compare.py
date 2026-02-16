import asyncio
import os
import chuscraper as zd
import json

async def main():
    print("🚀 Starting Google Shopping Scraper...")
    
    # Google is strict about IPs. Use good proxy.
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
            query = "Nike Air Jordan 1"
            print(f"🌍 Navigating to Google Shopping for '{query}'...")
            
            # Direct navigation to Shopping tab URL pattern
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=shop"
            page = await browser.get(url)
            
            # 3. Handle Consent Popup (Hybrid)
            try:
                if os.environ.get("GEMINI_API_KEY"):
                    await page.ai_pilot("If there is a cookie consent popup, click 'Reject all' or 'Accept all'.")
                else:
                    # Standard logic for consent with my new 'click' alias
                    # Try English, German, French buttons commonly found in EU
                    btns = ["Reject all", "Alle ablehnen", "Refuser tout", "I agree"]
                    for btn_text in btns:
                        # naive xpath check
                        found = await page.xpath(f"//button[contains(text(), '{btn_text}')]")
                        if found:
                            await found[0].click()
                            break
            except:
                pass

            # 4. Extract Comparison Data
            print("👀 Extracting prices...")
            
            if os.environ.get("GEMINI_API_KEY"):
                data = await page.ai_extract(
                    "Extract top 5 results with: product name, price, store name (merchant), and review score."
                )
            else:
                print("⚡ Standard Extraction...")
                data = []
                # Google Shopping selectors are messy classes like .i0X6df
                # We'll use a broad selector for product containers
                # This is fragile but demonstrates the concept
                items = await page.query_selector_all("div.sh-dgr__content")
                for item in items[:5]:
                     text = item.text
                     data.append({"raw_text": text[:150] + "..."})

            print("\n🎉 Comparison Data:\n")
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
