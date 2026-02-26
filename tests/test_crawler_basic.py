import asyncio
import logging
import os
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.INFO)

async def main():
    output_file = "test_basic_crawl.json"
    if os.path.exists(output_file):
        os.remove(output_file)

    print(f"--- TEST 1: Basic Crawl (JSON) ---")
    crawler = Crawler(
        start_urls=["https://revmerito.com"],
        max_pages=3,
        max_depth=1,
        concurrency=1,
        browser_config={"headless": True}
    )

    await crawler.run(output_file=output_file)

    if os.path.exists(output_file):
        print(f"✅ Success! {output_file} created.")
    else:
        print("❌ Failure: File not created.")

if __name__ == "__main__":
    asyncio.run(main())
