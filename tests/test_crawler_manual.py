import asyncio
import logging
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.DEBUG)

async def main():
    crawler = Crawler(
        start_urls=["https://revmerito.com"], # User's test target
        max_pages=3,
        max_depth=1,
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
