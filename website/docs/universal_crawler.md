---
sidebar_position: 5
---

# Universal Crawler

The **Universal Crawler** (`chuscraper.spider`) is a powerful, production-grade engine designed to crawl entire websites or specific subsections. It supports **BFS traversal**, **Sitemap parsing**, **concurrency**, and **streaming** out of the box.

Unlike the core `Browser` module which focuses on single-page interactions, the Crawler handles the complexity of queue management, link discovery, and data extraction for you.

## Quick Start

### Basic BFS Crawl

Crawl a website starting from a URL, following internal links up to a certain depth.

```python
import asyncio
from chuscraper.spider import Crawler

async def main():
    crawler = Crawler(
        start_urls=["https://example.com"],
        max_pages=10,        # Limit to 10 pages
        max_depth=2,         # Go 2 clicks deep
        concurrency=2,       # Run 2 tabs in parallel
        output_file="data.json" # Save results automatically
    )

    await crawler.run()
    print("Crawl complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Sitemap Crawl (Recommended)

For faster and more complete coverage, use the site's `sitemap.xml`. This skips the slow link discovery process.

```python
crawler = Crawler(
    sitemap_url="https://example.com/sitemap.xml",
    concurrency=5,
    output_file="sitemap_data.json"
)
await crawler.run()
```

## Features

### 1. Multi-Format Extraction
By default, the crawler extracts **Markdown** (optimized for LLMs). You can request multiple formats:

```python
crawler = Crawler(
    ...,
    formats=["markdown", "html", "text"] # Extract all three
)
```

### 2. Auto-Saving Files
The `crawler.run()` method supports automatic file saving in various formats:

- **JSON (`.json`)**: Structured data including all metadata.
- **CSV (`.csv`)**: Flattens data, great for spreadsheets.
- **JSONL (`.jsonl`)**: Line-delimited JSON, best for large datasets.
- **Markdown (`.md`)**: A single consolidated file containing all page content (perfect for RAG/LLM context).

```python
await crawler.run(output_file="knowledge_base.md")
```

### 3. Streaming / Callbacks (Infinite Scale)
For large-scale crawls (10k+ pages), storing data in memory creates bottlenecks. Use the `on_page_crawled` callback to process data immediately (e.g., save to DB) and free up RAM.

```python
async def save_to_db(data):
    # data = {'url': '...', 'title': '...', 'markdown': '...'}
    await db.insert(data)
    print(f"Saved: {data['url']}")

crawler = Crawler(
    start_urls=["https://large-site.com"],
    on_page_crawled=save_to_db # Pass the function
)

await crawler.run()
```

### 4. Single Page Mode
To scrape just one page without following links:

```python
crawler = Crawler(
    start_urls=["https://site.com/page"],
    max_pages=1,
    max_depth=0
)
```

### 5. AI Extraction (LLM)
You can attach an **AI Extractor** to turn raw text into structured JSON automatically.

```python
from chuscraper.ai import OpenAIExtractor

crawler = Crawler(
    start_urls=["https://site.com"],
    extractor=OpenAIExtractor(model="gpt-4o")
)

await crawler.run(prompt="Extract all pricing information")
```

👉 **[Read the Full AI Guide](ai_features.md)**

## Configuration Options

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `start_urls` | `List[str]` | `None` | Entry points for BFS crawling. |
| `sitemap_url` | `str` | `None` | URL of sitemap.xml (Overrides start_urls). |
| `max_pages` | `int` | `10` | Hard limit on number of pages to crawl. |
| `max_depth` | `int` | `2` | How many links deep to travel (0 = only start page). |
| `concurrency` | `int` | `2` | Number of simultaneous tabs/workers. |
| `formats` | `List[str]` | `["markdown"]` | `markdown`, `html`, `text`. |
| `browser_config` | `dict` | `None` | Config passed to `Browser.create()` (e.g. `{"headless": True}`). |

## Robustness & Stealth

The Crawler inherits all core `chuscraper` features:
- **Smart Redirects:** Handles domain changes (e.g. `example.com` -> `www.example.com`).
- **JS Fallback:** If Chrome fails to find links (SPA/React apps), it injects JavaScript to discover them manually.
- **Stealth:** Runs with full anti-detection (fingerprinting, webdriver hiding) enabled by default in the browser.
