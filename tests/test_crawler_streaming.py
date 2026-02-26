import asyncio
import logging
from chuscraper.spider import Crawler

logging.basicConfig(level=logging.INFO)

async def stream_handler(data):
    print(f"[STREAM] Got: {data['url']} ({len(data.get('markdown', ''))} chars)")

async def main():
    print(f"--- TEST 3: Streaming Crawl (Callback) ---")
    crawler = Crawler(
        start_urls=["https://revmerito.com"],
        max_pages=3,
        max_depth=1,
        concurrency=1,
        on_page_crawled=stream_handler,
        browser_config={"headless": True}
    )

    await crawler.run()
    print("✅ Success: Streaming finished without errors.")

if __name__ == "__main__":
    asyncio.run(main())
