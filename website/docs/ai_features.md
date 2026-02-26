---
sidebar_position: 7
---

# AI Extraction (LLM Integration)

Chuscraper transforms from a standard scraper to an intelligent data extraction engine using the `chuscraper.ai` module. By integrating with Large Language Models (LLMs) like OpenAI, you can extract structured JSON data from any website just by describing what you want.

## Why Use AI Extraction?

- **Zero Selectors:** Stop writing brittle CSS/XPath selectors that break when the site design changes.
- **Universal Logic:** Use the same prompt ("Extract pricing") for Amazon, Walmart, and eBay.
- **Structured Output:** Get clean JSON directly, ready for your database.

## Quick Start: OpenAIExtractor

Requires the `openai` package (`pip install openai`).

```python
import asyncio
import os
from chuscraper.spider import Crawler
from chuscraper.ai import OpenAIExtractor

async def main():
    # 1. Initialize the Extractor
    # Ensure OPENAI_API_KEY environment variable is set, or pass api_key="..."
    ai = OpenAIExtractor(model="gpt-4o")

    # 2. Setup Crawler with the AI Extractor
    crawler = Crawler(
        start_urls=["https://neurofiq.in"],
        max_pages=1,
        max_depth=0,
        extractor=ai # <--- Attach AI here
    )

    # 3. Run with a Natural Language Prompt
    results = await crawler.run(
        prompt="Extract the company mission, founder name, and a list of key services offered."
    )

    # 4. View Results
    for res in results:
        print(f"URL: {res['url']}")
        if "extracted_data" in res:
            print("AI Data:", res["extracted_data"])

if __name__ == "__main__":
    asyncio.run(main())
```

### Example Output

```json
{
  "mission": "To empower businesses with intelligent AI partners that enhance human capabilities...",
  "founder": "Toufiq Qureshi",
  "services": [
    "Business AI Analysis",
    "Answer Engine Optimization (AEO)",
    "AI Consulting & Strategy",
    "Web Scraping & Data Collection"
  ]
}
```

## How It Works

1.  **Crawl:** The `Crawler` visits the page and converts HTML to clean **Markdown**.
2.  **Prompt:** It combines your prompt with the Markdown content.
3.  **Inference:** It sends this to the LLM (e.g., OpenAI GPT-4o) with a request for JSON output.
4.  **Result:** The structured JSON is returned and saved in the `extracted_data` key of the result.

## Creating Custom Extractors

You can use any LLM (Anthropic, Gemini, Ollama) by creating a custom class that inherits from `BaseExtractor`.

```python
from chuscraper.ai import BaseExtractor
from typing import Dict, Optional

class MyOllamaExtractor(BaseExtractor):
    async def extract(self, content: str, prompt: str, schema: Optional[Dict] = None):
        # Call your local Ollama API here
        return {"data": "custom extraction logic"}
```

Then pass it to the crawler: `Crawler(..., extractor=MyOllamaExtractor())`.
