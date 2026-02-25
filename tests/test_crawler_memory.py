import asyncio
import logging
import os
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.INFO)

async def main():
    # Cleanup previous runs
    for f in ["crawl_results.json", "crawl_results.md", "crawl_results_formats.json"]:
        if os.path.exists(f):
            os.remove(f)

    crawler = Crawler(
        start_urls=["https://revmerito.com"],
        max_pages=1,
        max_depth=0,
        concurrency=1,
        # Request ALL formats
        formats=["markdown", "html", "text"],
        browser_config={"headless": True}
    )

    print("Starting Memory-Only Crawl with ALL Formats...")
    results = await crawler.run()

    # Check Result
    if results:
        data = results[0]
        keys = list(data.keys())
        print(f"\nKeys found in memory: {keys}")

        if "markdown" in data and "html" in data and "text" in data:
            print("✅ Success: All formats are present in memory.")
            print(f"Markdown Length: {len(data['markdown'])}")
            print(f"HTML Length: {len(data['html'])}")
            print(f"Text Length: {len(data['text'])}")
        else:
            print("❌ Failed: Missing formats.")
    else:
        print("❌ Failed: No results.")

if __name__ == "__main__":
    asyncio.run(main())
