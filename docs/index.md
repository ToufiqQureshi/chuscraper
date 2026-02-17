# Welcome to Chuscraper

**Chuscraper** is a high-performance, stealth-focused browser automation library for Python. Built on top of the Chrome DevTools Protocol (CDP), it manages to be faster and more undetectable than traditional Selenium or Puppeteer solutions.

## Why Chuscraper?

- **🚀 Blazing Fast**: Communicates directly with the browser via CDP, skipping the WebDriver overhead.
- **🥷 Stealth by Design**: Built-in anti-detection mechanisms to pass bot checks (Cloudflare, Akamai, etc.).
- **🤖 AI Powered**: Integrated LLM and Vision capabilities for intelligent extraction and self-healing selectors.
- **⚡ Async First**: Built on `asyncio` for high concurrency and performance.

## Key Features

| Feature | Description |
| :--- | :--- |
| **Direct CDP** | Full control over the browser protocol. |
| **Tab Management** | Easy multi-tab handling with efficient context switching. |
| **Smart Selectors** | CSS, XPath, and **Text** selectors with "best match" fuzzy logic. |
| **Undetected** | Patches `navigator`, `webdriver`, `WebGL`, and more automatically. |
| **Network Control** | Intercept requests, block URLs, and manage proxies effortlessly. |

## Getting Started

Check out the [Installation](installation.md) guide to get set up, or jump straight into [Your First Scraper](first_script.md).

## Example

```python
import asyncio
import chuscraper as zd

async def main():
    # Start browser with stealth enabled
    async with await zd.start(stealth=True) as browser:
        
        # Navigate to a site
        await browser.goto('https://example.com')
        
        # Extract data easily
        title = await browser.main_tab.title()
        heading = await browser.main_tab.select_text("h1")
        
        print(f"Site: {title}")
        print(f"Heading: {heading}")

if __name__ == '__main__':
    asyncio.run(main())
```
