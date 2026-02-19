import asyncio
import chuscraper as cs
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("shalimar_test")

async def run_browser_session(browser_id: int, url: str, proxy: str):
    prefix = f"[Browser-{browser_id}] "
    
    config = cs.Config(
        headless=False,
        stealth=True,
        proxy=proxy,
        timezone="Asia/Kolkata",
        browser_args=["--disable-gpu", "--start-maximized"]
    )
    
    logger.info(f"{prefix}🚀 Launching browser for {url}")
    
    try:
        async with await cs.start(config) as browser:
            logger.info(f"{prefix}✅ Browser launched (PID: {browser._process_pid})")
            
            tab = await browser.get(url)
            logger.info(f"{prefix}🌍 Navigated to {url}")
            
            # Extract title for confirmation
            title = await tab.evaluate("document.title")
            logger.info(f"{prefix}📝 Page Title: {title}")
            
            # User requested 2 minutes wait
            logger.info(f"{prefix}⏳ Waiting for 120 seconds (2 mins) as requested...")
            await asyncio.sleep(120)
            
            logger.info(f"{prefix}🏁 Session complete.")
            
    except Exception as e:
        logger.error(f"{prefix}❌ Error: {str(e)}")

async def main():
    proxy = "11de131690b3fdc7ba16__cr.in_12345:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"
    
    # 7 URLs provided by user
    urls = [
        "https://www.theshalimarhotel.com/",
        "https://www.theshalimarhotel.com/about.html",
        "https://www.theshalimarhotel.com/rooms.html",
        "https://www.theshalimarhotel.com/dining.html",
        "https://www.theshalimarhotel.com/event.html",
        "https://www.theshalimarhotel.com/gallery.html",
        "https://www.theshalimarhotel.com/contact.html"
    ]
    
    logger.info(f"🔥 Starting Shalimar Stress Test with {len(urls)} instances...")
    
    # Run all sessions concurrently
    tasks = [run_browser_session(i+1, url, proxy) for i, url in enumerate(urls)]
    await asyncio.gather(*tasks)
    
    logger.info("⭐ Stress Test Finished.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted.")
    except Exception as e:
        logger.error(f"💥 Main Error: {e}")
