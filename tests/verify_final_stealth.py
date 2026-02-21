import asyncio
import logging
import sys
from chuscraper import Browser, Config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("stealth_check")

logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("chuscraper.core.browser").setLevel(logging.INFO)

async def verify_stealth():
    logger.info("Starting browser with stealth enabled...")

    browser = await Browser.create(headless=True, stealth=True, sandbox=False)

    try:
        tab = await browser.get("data:text/html,<html><body>Stealth Check</body></html>")

        # 1. Check for CDC_ Variables (Should be gone)
        cdc_props = await tab.evaluate("""
            (() => {
                const regex = /cdc_[a-z0-9]/;
                const props = Object.getOwnPropertyNames(window);
                return props.filter(p => regex.test(p));
            })()
        """)

        if not cdc_props:
            logger.info("✅ CDC Variables removed successfully!")
        else:
            logger.error(f"❌ CDC Variables found: {cdc_props}")

        # 2. Check Permissions Mock
        perm_state = await tab.evaluate("""
            (async () => {
                try {
                    const res = await navigator.permissions.query({name: 'notifications'});
                    return res.state;
                } catch(e) { return 'error'; }
            })()
        """)
        logger.info(f"Notification Permission State: {perm_state}")

        # 3. Check WebDriver Hardening
        webdriver_check = await tab.evaluate("""
            (() => {
                const desc = Object.getOwnPropertyDescriptor(Navigator.prototype, 'webdriver');
                const val = navigator.webdriver;
                return { hasProp: !!desc, value: val };
            })()
        """)
        logger.info(f"WebDriver Check: {webdriver_check}")
        if webdriver_check.get('value') is False:
             logger.info("✅ WebDriver Property is False")
        else:
             logger.warning(f"⚠️ WebDriver Property leak: {webdriver_check}")

    except Exception as e:
        logger.error(f"❌ Verification Failed: {e}")
        # raise
    finally:
        await browser.stop()

if __name__ == "__main__":
    asyncio.run(verify_stealth())
