import asyncio
import logging
import os
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.INFO)

async def main():
    output_file = "crawl_results.md"
    if os.path.exists(output_file):
        os.remove(output_file)

    crawler = Crawler(
        start_urls=["https://neurofiq.in"],
        max_pages=2,
        max_depth=1,
        concurrency=1,
        browser_config={"headless": True}
    )

    print(f"Starting crawl... Saving to {output_file}")
    await crawler.run(output_file=output_file)

    if os.path.exists(output_file):
        print(f"Success! File {output_file} created.")
        with open(output_file, "r", encoding="utf-8") as f:
            print(f"File content preview:\n{f.read()[:300]}...")
    else:
        print("Error: File not created.")

if __name__ == "__main__":
    asyncio.run(main())
