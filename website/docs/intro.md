# Welcome to Chuscraper

**Chuscraper** is a high-performance, stealth-focused browser automation library for Python. Built on top of the Chrome DevTools Protocol (CDP), it manages to be faster and more undetectable than traditional Selenium or Puppeteer solutions.

## Why Chuscraper?

- **🚀 Blazing Fast**: Communicates directly with the browser via CDP, skipping the WebDriver overhead.
- **🥷 Stealth by Design**: Built-in anti-detection mechanisms to pass bot checks (Cloudflare, Akamai, etc.) out of the box.
- **⚡ Async First**: Built on `asyncio` for high concurrency and modern performance.
- **🧩 Modular & Easy**: New Mixin-based architecture makes it powerful yet simple to use.

## Key Features

| Feature | Description |
| :--- | :--- |
| **Direct CDP** | Full control over the browser protocol. |
| **Tab Management** | Easy multi-tab handling with `browser.tabs` and `browser.get()`. |
| **Smart Selectors** | CSS, XPath, and **Text** selectors with "best match" fuzzy logic. |
| **Undetected** | Automatic patching of `navigator`, `webdriver`, `WebGL`, and more. |
| **Network Control** | Intercept requests, block URLs, and manage cookies effortlessly. |

## Quick Example

```python
import asyncio
import chuscraper as cs

async def main():
    # Start browser with stealth enabled (undiscovered mode)
    async with await cs.start(stealth=True) as browser:
        
        # Navigate simply
        tab = await browser.get('https://example.com')
        
        # Extract data in one line
        title = await tab.title()
        heading = await tab.find("Example Domain")
        
        print(f"Site: {title}")
        print(f"Heading Text: {await heading.text()}")

if __name__ == '__main__':
    asyncio.run(main())
```

Check out the [Installation](installation.md) guide to get set up, or dive into the [Quickstart](quickstart.md).
