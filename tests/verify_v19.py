import asyncio
import logging
import chuscraper
from chuscraper import Logger
import os
import json

# Logging setup
Logger.setup(logging.INFO)
logger = logging.getLogger("verify_v19")

PROXY_URL = "http://11de131690b3fdc7ba16__cr.in:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"

TARGET_SITES = [
    "https://pixelscan.net/",
    "https://abrahamjuliot.github.io/creepjs/",
    "https://browserleaks.com/webgl",
]

async def run_audit(url: str, stats: dict):
    logger.info(f"🚀 [VERIFY] Launching for: {url}")

    browser = await chuscraper.start(
        headless=False,
        proxy=PROXY_URL,
        stealth=True, 
        expert=True,
    )

    try:
        page = await browser.get(url)
        logger.info(f"✅ Loaded {url}. Waiting for diagnostics...")

        await asyncio.sleep(20) # Wait for fingerprinting to finish

        # Extract basic diagnostics for the report
        info = {}
        try:
            info['ua'] = await page.evaluate("navigator.userAgent")
            info['platform'] = await page.evaluate("navigator.platform")
            info['webdriver'] = await page.evaluate("navigator.webdriver")
            info['timezone'] = await page.evaluate("Intl.DateTimeFormat().resolvedOptions().timeZone")
            
            # WebGL Info
            info['webgl_vendor'] = await page.evaluate("(() => { const c = document.createElement('canvas'); const gl = c.getContext('webgl'); const debug = gl.getExtension('WEBGL_debug_renderer_info'); return debug ? gl.getParameter(debug.UNMASKED_VENDOR_WEBGL) : 'N/A'; })()")
            info['webgl_renderer'] = await page.evaluate("(() => { const c = document.createElement('canvas'); const gl = c.getContext('webgl'); const debug = gl.getExtension('WEBGL_debug_renderer_info'); return debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : 'N/A'; })()")
        except Exception as e:
            logger.debug(f"Diag failed: {e}")
        
        stats[url] = info

        filename = "verify_" + url.split("//")[1].replace(".", "_").replace("/", "_") + ".png"
        await page.save_screenshot(filename, full_page=True)
        logger.info(f"📸 Screenshot saved as {filename}")

    except Exception as e:
        logger.error(f"❌ Error during verification of {url}: {e}")
    finally:
        await browser.stop()

async def main():
    logger.info("🛠️ Starting v0.19.0 (2026 Update) Verification Run...")
    stats = {}
    for site in TARGET_SITES:
        await run_audit(site, stats)
    
    # Print Summary Table
    print("\n" + "="*80)
    print(f"{'SITE':<40} | {'WEBDRIVER':<10} | {'TIMEZONE':<20}")
    print("-" * 80)
    for site, info in stats.items():
        print(f"{site[:40]:<40} | {str(info.get('webdriver')):<10} | {info.get('timezone', 'N/A'):<20}")
    
    print("\n" + "="*80)
    print("DETAIL DIAGNOSTICS:")
    for site, info in stats.items():
        print(f"\n[ {site} ]")
        for k, v in info.items():
            print(f"  {k}: {v}")
    
    print("\n🎉 Verification Run Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(main())
