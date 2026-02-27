import asyncio
import logging
from chuscraper.spider import Crawler
from chuscraper.ai import BaseExtractor

# Mock Extractor for Testing
class MockExtractor(BaseExtractor):
    async def extract(self, content, prompt, schema=None):
        return {
            "mock_data": "Extracted Successfully",
            "prompt_received": prompt,
            "content_length": len(content)
        }

logging.basicConfig(level=logging.INFO)

async def main():
    print("--- TEST: AI Extraction (Mock) ---")

    # 1. Initialize Mock AI
    ai = MockExtractor()

    # 2. Run Crawler with Extractor
    crawler = Crawler(
        start_urls=["https://revmerito.com"],
        max_pages=1,
        max_depth=0,
        concurrency=1,
        extractor=ai, # Pass AI
        browser_config={"headless": True}
    )

    # 3. Request Extraction
    results = await crawler.run(prompt="Extract everything")

    if results:
        data = results[0]
        if "extracted_data" in data:
            print("✅ PASS: AI Extraction hook triggered.")
            print(f"Result: {data['extracted_data']}")
        else:
            print("❌ FAIL: 'extracted_data' key missing.")
    else:
        print("❌ FAIL: No results.")

if __name__ == "__main__":
    asyncio.run(main())
