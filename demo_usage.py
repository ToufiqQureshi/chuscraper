import asyncio
import chuscraper
import logging

# Optional: Enable logging to see what's happening
logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Configure Browser with Stealth & Proxy
    # Replace with your actual proxy details
    proxy_url = "http://11de131690b3fdc7ba16__cr.in:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"
    
    print("Starting Chuscraper with Stealth Mode...")
    browser = await chuscraper.start(
        proxy=proxy_url,        # Automatic auth extension created
        stealth=True,           # Hides navigator.webdriver, mocks permissions
        timezone="Asia/Kolkata", # Matches your proxy location
        headless=False          # Set to True for background running
    )

    # 2. Open a page to test
    print("Navigating to check IP and detection...")
    page = await browser.get("https://whoer.net") # Good site to see your IP/DNS/System info

    # 3. Wait a bit to see the result (if headless=False)
    await asyncio.sleep(10)
    
    # 4. Do your scraping here...
    # content = await page.get_content()
    # print(content)

    # 5. Close browser
    print("Closing browser...")
    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
