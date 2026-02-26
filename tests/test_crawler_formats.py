import asyncio
import logging
import os
import json
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.INFO)

async def main():
    output_file = "test_formats_crawl.md"
    if os.path.exists(output_file):
        os.remove(output_file)

    print(f"--- TEST 2: Multi-Format Crawl (Markdown + HTML) ---")
    crawler = Crawler(
        start_urls=["https://revmerito.com"],
        max_pages=2,
        max_depth=1,
        concurrency=1,
        formats=["markdown", "html", "text"], # Requesting ALL
        browser_config={"headless": True}
    )

    # Note: Saving to .md will only write the 'markdown' part, but we can inspect memory results
    results = await crawler.run(output_file=output_file)

    if os.path.exists(output_file):
        print(f"✅ Success! {output_file} created.")

        # Verify in-memory data has all formats
        if results and "html" in results[0] and "text" in results[0]:
             print("✅ Success: In-memory data contains HTML and Text.")
        else:
             print("❌ Failure: Missing formats in memory.")
    else:
        print("❌ Failure: File not created.")

if __name__ == "__main__":
    asyncio.run(main())
