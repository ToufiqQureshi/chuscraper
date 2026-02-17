import asyncio
import chuscraper
import traceback
import sys

async def test():
    print("Starting test...")
    try:
        browser = await chuscraper.start(headless=True)
        print("Browser started.")
        page = await browser.get("https://example.com")
        print("Page loaded.")
        title = await page.evaluate("document.title")
        print(f"Title: {title}")
    except Exception as e:
        print(f"Error caught in test: {e}")
        traceback.print_exc()
    finally:
        try:
            await browser.stop()
            print("Browser stopped.")
        except:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(test())
    except Exception as e:
        print(f"Error in main: {e}")
        traceback.print_exc()
