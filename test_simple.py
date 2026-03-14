import asyncio
import chuscraper as zd
import base64

async def test_simple():
    async with await zd.start(headless=True) as browser:
        page = browser.main_tab
        html = "<html><body><h1>Test Header</h1></body></html>"
        data_url = f"data:text/html;base64,{base64.b64encode(html.encode()).decode()}"
        await page.goto(data_url)
        print(f"Navigated to data URL. Current URL: {page.url}")

        try:
            h1 = await page.select("h1", timeout=5)
            print(f"H1 found: '{h1.text_all}'")
        except Exception as e:
            print(f"H1 not found: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple())
