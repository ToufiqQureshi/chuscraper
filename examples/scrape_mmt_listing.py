import asyncio
import logging
from chuscraper import start

# 1. Proxy Config (DataImpulse)
# Connects via Local Auth Proxy for 100% stealth & no popups
PROXY = "http://11de131690b3fdc7ba16__cr.in:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"

# 2. Target URL (MMT Listing)
URL = "https://www.makemytrip.com/hotels/hotel-listing/?checkin=02142026&checkout=02152026&locusId=CTPERI&locusType=city&city=CTPERI&country=IN&searchText=Avalon%20Homes&roomStayQualifier=1e0e&_uCurrency=INR&reference=hotel&rf=directSearch&lat=10.980447&lng=76.22101&topHtlId=202402081435047513&type=hotel&rsc=1e1e0e"

async def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    print("🚀 Launcing Chuscraper with Stealth & Local Proxy...")

    # 3. Start Browser
    # stealth=True activates Patchright-style anti-detection
    browser = await start(
        proxy=PROXY,
        stealth=True,
        timezone="Asia/Kolkata",
        headless=False,
        browser_args=["--start-maximized"]
    )

    try:
        # 4. Optional: Verify IP First
        print("🕵️ Checking Proxy IP...")
        ip_page = await browser.get("https://api.ipify.org", new_tab=True)
        await asyncio.sleep(2)
        print(f"✅ Current IP: {await ip_page.evaluate('document.body.innerText')}")
        await ip_page.close()

        # 5. Navigate to MMT
        print(f"🌍 Navigating to MMT Listing...")
        page = await browser.get(URL)
        
        # 6. Wait for 200 Seconds as requested
        print("⏳ Reached Target. Waiting for 200 seconds...")
        await asyncio.sleep(200)
        
        print("📸 Taking screenshot before exit...")
        await page.save_screenshot("mmt_listing_proof.png")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("🛑 STOPPING BROWSER")
        await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
