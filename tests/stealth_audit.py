import asyncio
import logging
import chuscraper
from chuscraper.core.observability import Logger

# Logging setup
Logger.setup(logging.INFO)
logger = logging.getLogger("stealth_audit")

# User Proxy Config
PROXY_URL = "http://11de131690b3fdc7ba16__cr.in:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"

# Target Sites
TARGET_SITES = [
    "https://www.browserscan.net/",
    "https://abrahamjuliot.github.io/creepjs/",
    "https://bot.sannysoft.com/",
    "https://pixelscan.net/",
    "https://browserleaks.com/ip"
]

async def run_audit(url: str):
    logger.info(f"🚀 Launching new Chrome instance for: {url}")
    
    # Each launch is a separate "instance" (clean profile/process context)
    browser = await chuscraper.start(
        headless=False, # Set to True for production, False to see results
        proxy=PROXY_URL,
        expert=True, # Enable shadow DOM piercing and expert stealth
    )
    
    try:
        page = await browser.get(url)
        logger.info(f"✅ Loaded {url}. Waiting 5 minutes (300s) as requested...")
        
        # Wait 5 minutes
        await asyncio.sleep(300)
        
        # Take a screenshot before closing for proof
        filename = url.split("//")[1].split(".")[1] + "_audit.png"
        await page.save_screenshot(filename, full_page=True)
        logger.info(f"📸 Screenshot saved as {filename}")

    except Exception as e:
        logger.error(f"❌ Error auditing {url}: {e}")
    finally:
        await browser.stop()
        logger.info(f"🏁 Instance closed for {url}")

async def main():
    # Running them sequentially to avoid overwhelming system resources
    # since each one waits 5 minutes.
    for site in TARGET_SITES:
        await run_audit(site)

if __name__ == "__main__":
    asyncio.run(main())
