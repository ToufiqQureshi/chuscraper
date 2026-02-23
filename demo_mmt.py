import asyncio
import logging
import os
from chuscraper.core.browser import Browser
from chuscraper.core.stealth import SystemProfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_test():
    url = "https://www.makemytrip.com/hotels/hotel-listing/?checkin=02232026&checkout=02242026&locusId=CTJAI&locusType=city&city=CTJAI&country=IN&searchText=Cygnett%20Style%20Ganga%20Hotel&roomStayQualifier=1e0e&_uCurrency=INR&reference=hotel&rf=directSearch&lat=26.814932&lng=75.86291&topHtlId=202311282002508888&type=hotel&rsc=1e1e0e"
    
    # Proxy configuration
    proxy_server = "gw.dataimpulse.com:823"
    proxy_user = "11de131690b3fdc7ba16__cr.in"
    proxy_pass = "e3e7d1a8f82bd8e3"
    
    proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_server}"
    
    logger.info("Initializing Browser with Proxy...")
    # Initialize Browser using create method for proper setup
    browser = await Browser.create(proxy=proxy_url)
    async with browser:
        tab = await browser.get(url)
        
        logger.info("Applying Advanced Stealth...")
        profile = SystemProfile.from_system(cookie_domain="makemytrip.com")
        await profile.apply(tab)
        
        logger.info(f"Navigating to: {url}")
        # Wait for page to load more content
        await asyncio.sleep(8) 
        
        # Try to extract hotel name using the new select_one method
        # The engine logic might need a bit more time for complex DOMs
        hotel_name_elem = await tab.select_one("h1.hotelName") 
        if hotel_name_elem:
            name = await hotel_name_elem.to_text()
            logger.info(f"SUCCESS! Found Hotel Name: {name}")
        else:
            logger.warning("Could not find hotel name with h1.hotelName, checking content...")
            # Fallback to general title or body text
            content_snippet = await tab.to_text(main_content_only=True)
            logger.info(f"Main Content Snippet: {content_snippet[:500]}...")
            
        # Take a screenshot for verification
        screenshot_path = "mmt_result.png"
        await tab.save_screenshot(screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")

if __name__ == "__main__":
    asyncio.run(run_test())
