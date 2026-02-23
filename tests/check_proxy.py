import asyncio
import chuscraper
import logging

logging.basicConfig(level=logging.INFO)

async def check_proxy():
    PROXY_URL = "http://11de131690b3fdc7ba16__cr.in:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"
    print("🌐 Checking Proxy Status...")
    
    browser = await chuscraper.start(
        stealth=True,
        proxy=PROXY_URL,
        browser_args=["--disable-http2"]
    )

    try:
        tab = browser.main_tab
        await tab.goto("https://api.ipify.org?format=json")
        await asyncio.sleep(5)
        text = await tab.evaluate("document.body.innerText")
        print(f"📡 Response Body: {text}")

        # Try another site
        await tab.goto("https://www.google.com")
        await asyncio.sleep(5)
        title = await tab.title()
        print(f"🏠 Google Title: {title}")

    except Exception as e:
        print(f"[✘] Error: {e}")
    finally:
        await browser.stop()

if __name__ == "__main__":
    asyncio.run(check_proxy())
