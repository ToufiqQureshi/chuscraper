import asyncio
import logging
import chuscraper
from chuscraper import Logger
import os

# Logging setup
Logger.setup(logging.INFO)
logger = logging.getLogger("verify_v19")

PROXY_URL = "http://11de131690b3fdc7ba16__cr.in:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"

# Testing 2 key sites with much shorter wait
TARGET_SITES = [
    "https://www.browserscan.net/",
    "https://bot.sannysoft.com/",
    "https://abrahamjuliot.github.io/creepjs/"
]

async def run_audit(url: str):
    logger.info(f"🚀 [VERIFY] Launching for: {url}")

    browser = await chuscraper.start(
        headless=False,  # Headless False to see results
        proxy=PROXY_URL,
        expert=True,
    )

    try:
        page = await browser.get(url)
        logger.info(f"✅ Loaded {url}. Waiting 30s for stability check...")

        await asyncio.sleep(30) # CreepJS needs time to calculate fingerprint

        filename = "verify_" + url.split("//")[1].split(".")[1] + ".png"
        if "creepjs" in url:
            filename = "verify_creepjs.png"
        await page.save_screenshot(filename, full_page=True)
        logger.info(f"📸 Screenshot saved as {filename}")
        
        if os.path.exists(filename):
            logger.info(f"🌟 SUCCESS: {filename} exists!")
        else:
            logger.error(f"❌ FAILURE: {filename} not found!")

    except Exception as e:
        logger.error(f"❌ Error during verification of {url}: {e}")
        raise
    finally:
        await browser.stop()
        logger.info(f"🏁 Instance closed for {url}")

async def main():
    logger.info("🛠️ Starting v0.19.0 Verification Run...")
    for site in TARGET_SITES:
        await run_audit(site)
    logger.info("🎉 Verification Run Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(main())
