import asyncio
import logging
import os
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.INFO)

async def main():
    output_file = "sitemap_results.json"
    if os.path.exists(output_file):
        os.remove(output_file)

    # Use a known public sitemap or local if possible.
    # Neurofiq might not have one, let's try or assume it does for the test structure.
    # If fetch fails, it handles gracefully.
    target_sitemap = "https://neurofiq.in/sitemap.xml"

    print(f"--- TEST 4: Sitemap Crawl ---")
    crawler = Crawler(
        sitemap_url=target_sitemap,
        max_pages=5, # Limit to avoid crawling whole site
        max_depth=1, # Depth from sitemap URLs
        concurrency=1,
        browser_config={"headless": False}
    )

    await crawler.run(output_file=output_file)

    if os.path.exists(output_file):
        print(f"Success! {output_file} created.")
        with open(output_file, encoding="utf-8") as f:
            import json
            data = json.load(f)
            print(f"Crawled {len(data)} pages from sitemap source.")
    else:
        print("Failure: File not created (Maybe sitemap doesn't exist or failed to parse).")

if __name__ == "__main__":
    asyncio.run(main())
