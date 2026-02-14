"""
Scrape MakeMyTrip Hotel Details using Chuscraper (Patchright Architecture).
Demonstrates:
- Local Proxy Auth (No Popups)
- Advanced Stealth (Bypass Anti-Bot)
- Robust Navigation
"""
import asyncio
import logging
import chuscraper
from chuscraper import start

# 1. Proxy Configuration (DataImpulse)
# The Local Proxy will handle authentication transparently.
PROXY = "http://11de131690b3fdc7ba16__cr.in:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"

# 2. Target URL
URL = "https://www.makemytrip.com/hotels/hotel-details/?hotelId=202311282002508888&_uCurrency=INR&checkin=02142026&checkout=02152026&city=CTJAI&country=IN&lat=26.81493&lng=75.86291&locusId=CTJAI&locusType=city&rank=1&reference=hotel&rf=directSearch&roomStayQualifier=1e0e&rsc=1e1e0e&searchText=Cygnett%20Style%20Ganga%20Hotel&topHtlId=202311282002508888&type=hotel&mtkeys=undefined"

async def main():
    # Setup logging to see what's happening
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("mmt_scraper")
    
    print(f"🚀 Starting Scraper...\nProxy: {PROXY}\nTarget: MMT (Cygnett Style Ganga)")

    # 3. Launch Browser with Upgraded Features
    # - proxy: Automatically triggers LocalAuthProxy (Patchright Arch)
    # - stealth: Activates new evasion scripts (webdriver=undefined)
    browser = await start(
        proxy=PROXY,
        stealth=True,
        timezone="Asia/Kolkata",  # Match MMT's expected timezone
        headless=False,           # Visible for debugging
        browser_args=["--start-maximized"] # Full screen for better rendering
    )

    try:
        # 4. Verify IP (Optional but good for debugging)
        logger.info("Verifying Proxy IP...")
        ip_page = await browser.get("https://api.ipify.org", new_tab=True)
        await asyncio.sleep(2)
        ip = await ip_page.evaluate("document.body.innerText")
        logger.info(f"Current Scraper IP: {ip}")
        await ip_page.close()

        # 5. Navigate to Hotel URL
        logger.info("Navigating to Hotel Page...")
        # Note: browser.get() now robustly handles new tab creation if needed
        # But for the first navigation, we can just use the main tab or get()
        page = await browser.get(URL)

        # 5. Wait for Content
        logger.info("Waiting for page to load...")
        # Wait for the H1 tag to ensure the main content is rendered
        # MMT is heavy, let's give it some time
        await asyncio.sleep(10) 
        
        # 6. Extract Data
        # Using pure JS evaluation for reliability
        data = await page.evaluate("""
            () => {
                // MMT basics
                // Name Selectors (Try multiple)
                const name = document.getElementById('hlistpg_hotel_name')?.innerText || 
                             document.querySelector('h1')?.innerText || 
                             document.querySelector('.prmProperty__name')?.innerText ||
                             document.querySelector('.hotelName')?.innerText;
                
                // Check if sold out
                const bodyText = document.body.innerText;
                const soldOut = bodyText.includes("Not available for selected dates") || 
                                bodyText.includes("You Just Missed It") ||
                                bodyText.includes("Sold Out");
                
                let price = "Sold Out";
                if (!soldOut) {
                    const priceDiv = document.querySelector('.prmRoomDet__infoCol .prmRoomDet__priceVal') || 
                                     document.querySelector('#hlistpg_hotel_shown_price');
                    if (priceDiv) price = priceDiv.innerText;
                    else price = "Price Not Found (Selectors Failed)";
                } else {
                     // Try to get alternative price
                     const altPrice = document.querySelector('.rateCard__price');
                     if (altPrice) price = "Sold Out (Alt: " + altPrice.innerText + ")";
                }

                const rating = document.querySelector('.hotelRating__ratingSummary')?.innerText || 
                               document.querySelector('#hlistpg_hotel_user_rating')?.innerText;
                
                return {
                    name: name || "Not Found (Body Len: " + bodyText.length + ")",
                    price: price || "Not Found",
                    rating: rating || "No Rating"
                };
            }
        """)

        print("\n" + "="*40)
        print("🏨 EXTRACTED HOTEL DATA")
        print("="*40)
        print(f"Name   : {data.get('name')}")
        print(f"Price  : {data.get('price')}")
        print(f"Rating : {data.get('rating')}")
        print("="*40 + "\n")
        
        # Take a screenshot as proof
        await page.save_screenshot("mmt_cygnett_proof.png")
        print("📸 Proof saved as mmt_cygnett_proof.png")

        # Keep open for visual inspection
        print("👀 Keeping browser open for 30s...")
        await asyncio.sleep(30)

    except Exception as e:
        logger.error(f"Scraping Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.stop()
        print("✅ Browser Closed")

if __name__ == "__main__":
    asyncio.run(main())
