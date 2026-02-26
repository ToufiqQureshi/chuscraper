# Universal Crawler

Chuscraper includes a high-performance **Universal Crawler** designed for multi-page, concurrent data extraction. It follows a Breadth-First Search (BFS) pattern and can handle large-scale crawling tasks with ease.

## Key Features

- **BFS Traversal**: Systematically explores links up to a defined depth.
- **High Concurrency**: Utilizes multiple browser tabs to speed up extraction.
- **Domain Bound**: Automatically stays within the allowed domain to prevent runaway crawls.
- **Structured Outputs**: Direct export to JSON, JSONL, CSV, and Markdown.
- **Sitemap Support**: Can ingest `sitemap.xml` files to discover URLs efficiently.
- **Streaming Mode**: Process pages as they are crawled via async callbacks.

## Basic Usage

To start a crawl, you only need a starting URL.

```python
import asyncio
from chuscraper.spider import Crawler

async def main():
    # Initialize the crawler
    crawler = Crawler(
        start_urls=["https://example.com"],
        max_pages=20,
        max_depth=2,
        concurrency=3
    )

    # Run and save to JSON
    results = await crawler.run(output_file="results.json")
    print(f"Crawled {len(results)} pages.")

if __name__ == "__main__":
    asyncio.run(main())
```

## Crawling with Sitemaps

If a website provides a sitemap, the Crawler can use it to find all relevant pages instantly.

```python
crawler = Crawler(
    sitemap_url="https://example.com/sitemap.xml",
    max_pages=100,
    concurrency=5
)
await crawler.run(output_file="site_data.jsonl")
```

## Advanced Extraction Hooks

By default, the Crawler extracts the title and a Markdown version of the page. You can customize this by providing an `extraction_hook`.

```python
async def my_custom_extractor(tab):
    # This function runs on every page crawled
    return {
        "url": tab.url,
        "h1": await (await tab.select("h1")).text(),
        "price": await (await tab.find("$")).text(),
    }

crawler = Crawler(
    start_urls="https://shop.com",
    extraction_hook=my_custom_extractor
)
await crawler.run(output_file="prices.csv")
```

## Streaming Callbacks

For very large crawls where you don't want to keep everything in memory, use `on_page_crawled`.

```python
async def save_to_db(data):
    # data contains extracted page info
    print(f"Saving {data['url']} to database...")

crawler = Crawler(
    start_urls="https://news.com",
    on_page_crawled=save_to_db
)
await crawler.run()
```

## API Reference: `Crawler`

### Constructor Arguments

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `start_urls` | `List[str] \| str` | `None` | The URL(s) where the crawl begins. |
| `sitemap_url` | `str` | `None` | URL to a `sitemap.xml`. Overrides `start_urls`. |
| `max_pages` | `int` | `10` | Limit on total unique pages to visit. |
| `max_depth` | `int` | `2` | Max depth from the starting URL. |
| `concurrency` | `int` | `2` | Number of simultaneous browser tabs. |
| `formats` | `List[str]` | `["markdown"]` | Formats to extract: `markdown`, `html`, `text`. |
| `browser_config`| `dict` | `{}` | Arguments passed to `Browser.create()`. |
| `extraction_hook`| `callable` | `None` | Custom async function to extract data from a `Tab`. |
| `on_page_crawled`| `callable` | `None` | Async callback called for every page. |

### `run()` Method

| Argument | Type | Description |
| :--- | :--- | :--- |
| `output_file` | `str` | File path to save results (`.json`, `.csv`, `.jsonl`, `.md`). |
| `prompt` | `str` | (Future) LLM prompt for extraction. |
| `schema` | `Any` | (Future) Pydantic schema for extraction. |
