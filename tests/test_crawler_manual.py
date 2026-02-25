import asyncio
import logging
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.INFO)

async def main():
    crawler = Crawler(
        start_urls=["https://revmerito.com"],
        max_pages=10,
        max_depth=3, # Increased depth to find deeper pages
        concurrency=1,
        browser_config={"headless": True}
    )

    print("Starting crawl with Depth 3...")
    results = await crawler.run()

    print(f"Crawled {len(results)} pages.")
    for res in results:
        print(f"URL: {res.get('url')}")
        print(f"Title: {res.get('title')}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())
