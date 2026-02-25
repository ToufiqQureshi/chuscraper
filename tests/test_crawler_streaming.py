import asyncio
import logging
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.INFO)

async def process_page(data):
    """
    Simulates saving to a database or streaming.
    """
    print(f"\n[STREAM] Received Page: {data['url']}")
    print(f"[STREAM] Title: {data['title']}")
    # print(f"[STREAM] Content Length: {len(data.get('markdown', ''))}")
    # In a real app, you would: await db.save(data)

async def main():
    crawler = Crawler(
        start_urls=["https://revmerito.com"],
        max_pages=3,
        max_depth=1,
        concurrency=1,
        on_page_crawled=process_page, # Pass the callback
        browser_config={"headless": True}
    )

    print("Starting Streaming Crawl...")
    # output_file is ignored when streaming
    await crawler.run()

    print("\nCrawl Completed.")

if __name__ == "__main__":
    asyncio.run(main())
