import asyncio
import logging
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.INFO)

async def main():
    crawler = Crawler(
        start_urls=["https://revmerito.com"],
        max_pages=5, # Increased to ensure we see depth
        max_depth=2,
        concurrency=1,
        browser_config={"headless": True}
    )

    print("Starting crawl...")
    results = await crawler.run()

    print(f"Crawled {len(results)} pages.")
    for res in results:
        print(f"URL: {res.get('url')}")
        print(f"Title: {res.get('title')}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())
