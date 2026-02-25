import asyncio
import logging
import os
import json
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.INFO)

async def main():
    output_file = "crawl_results_formats.json"
    if os.path.exists(output_file):
        os.remove(output_file)

    crawler = Crawler(
        start_urls=["https://revmerito.com"],
        max_pages=2,
        max_depth=1,
        concurrency=1,
        formats=["markdown", "html"], # Request both formats
        browser_config={"headless": True}
    )

    print(f"Starting crawl... Saving to {output_file}")
    await crawler.run(output_file=output_file)

    if os.path.exists(output_file):
        print(f"Success! File {output_file} created.")
        with open(output_file, "r") as f:
            data = json.load(f)
            if data and "markdown" in data[0] and "html" in data[0]:
                print("Verification Passed: Both markdown and html present.")
            else:
                print("Verification Failed: Missing formats.")
    else:
        print("Error: File not created.")

if __name__ == "__main__":
    asyncio.run(main())
