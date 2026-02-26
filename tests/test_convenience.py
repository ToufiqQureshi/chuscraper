import asyncio
import logging
import chuscraper as cs
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO)

class Product(BaseModel):
    name: Optional[str] = None
    price: Optional[str] = None

async def test_scrape():
    print("--- Testing cs.scrape() ---")
    try:
        data = await cs.scrape("https://example.com", wait=1)
        print(f"URL: {data.get('url')}")
        print(f"Title: {data.get('title')}")
        if 'markdown' in data:
            print("✅ Markdown extracted")
        else:
            print("❌ Markdown missing")
    except Exception as e:
        print(f"❌ Scrape failed: {e}")

async def test_extract():
    print("\n--- Testing Tab.extract() with Pydantic ---")
    async with await cs.start(headless=True) as browser:
        tab = await browser.get("https://example.com")
        product = await tab.extract(Product)
        print(f"Extracted Product: {product}")
        print("✅ Extract call finished (Logic is rule-based fallback for now)")

async def main():
    await test_scrape()
    await test_extract()

if __name__ == "__main__":
    asyncio.run(main())
