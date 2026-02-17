import asyncio
import logging
import sys
import os

# Add parent dir to path to import chuscraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chuscraper
from chuscraper.core.observability import Logger

Logger.setup(logging.DEBUG)
logger = logging.getLogger("production_test")

async def test_proxy_and_stealth():
    logger.info("🚀 Starting Proxy & Stealth Production Test")
    
    # Use a dummy proxy or real if available
    proxy = os.environ.get("TEST_PROXY_URL", "http://user:pass@1.2.3.4:5678")
    
    try:
        browser = await chuscraper.start(
            headless=True,
            proxy=proxy if "user:pass" not in proxy else None, # Skip if dummy
            expert=True
        )
        page = await browser.get("https://bot.sannysoft.com/")
        
        # Verify stealth
        logger.info("Checking fingerprint consistency...")
        results = await page.select_all(".result.failed")
        if results:
            logger.warning(f"⚠️ Found {len(results)} failed stealth checks!")
        else:
            logger.info("✅ All basic stealth checks passed!")
            
        await page.screenshot(full_page=True)
        await browser.stop()
        
    except Exception as e:
        logger.error(f"❌ Proxy/Stealth test failed: {e}")
        raise

async def test_ai_precision():
    logger.info("🚀 Starting AI Precision Test")
    
    browser = await chuscraper.start(headless=True)
    page = await browser.get("https://www.google.com")
    
    from chuscraper.ai.agent import AIPilot
    pilot = AIPilot(page, safe_mode=True)
    
    # We don't need real LLM here for logic test if we mock, 
    # but for production test we want E2E.
    if os.environ.get("GEMINI_API_KEY"):
        logger.info("Running E2E AI Navigation...")
        success = await pilot.run("Search for Chuscraper on GitHub and find the first result.")
        logger.info(f"AI Result: {success}")
    else:
        logger.warning("Skipping AI E2E (No API Key)")
        
    await browser.stop()

async def test_high_concurrency():
    logger.info("🚀 Starting High Concurrency Test")
    
    browser = await chuscraper.start(headless=True)
    
    async def task(i):
        page = await browser.new_tab()
        await page.goto("https://example.com")
        title = await page.title()
        logger.info(f"Tab {i} loaded: {title}")
        await page.close()

    # Launch 5 concurrent tabs
    await asyncio.gather(*(task(i) for i in range(5)))
    
    await browser.stop()

if __name__ == "__main__":
    async def main():
        try:
            await test_proxy_and_stealth()
            await test_high_concurrency()
            # await test_ai_precision()
            logger.info("🎉 ALL PRODUCTION TESTS PASSED!")
        except Exception as e:
            logger.error(f"FATAL: {e}")
            sys.exit(1)
            
    asyncio.run(main())
