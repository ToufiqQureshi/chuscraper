import asyncio
import logging
import os
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.INFO)

async def main():
    # Define files
    files = ["output_test.json", "output_test.csv", "output_test.jsonl", "output_test.md"]

    # Cleanup
    for f in files:
        if os.path.exists(f):
            os.remove(f)

    # Crawl ONCE
    crawler = Crawler(
        start_urls=["https://revmerito.com"],
        max_pages=2,
        max_depth=1,
        concurrency=1,
        browser_config={"headless": True}
    )
    print("Crawling once...")
    await crawler.run() # Data in memory

    # Save manually to test the internal logic (using internal method for test)
    # Ideally we run crawler.run(output_file=...) 3 times, but that's slow.
    # We will hack it to call _save_to_file multiple times for verification.

    print("\nSaving files...")
    for f in files:
        crawler._save_to_file(f)
        if os.path.exists(f):
            print(f"✅ Created: {f}")
        else:
            print(f"❌ Failed: {f}")

if __name__ == "__main__":
    asyncio.run(main())
