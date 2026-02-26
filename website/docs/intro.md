# Welcome to Chuscraper 🕷️

<p align="center">
  <img src="https://i.ibb.co/HLyG7BBK/Chat-GPT-Image-Feb-16-2026-11-13-14-AM.png" alt="Chuscraper Logo" width="180" />
</p>

**Chuscraper** is a high-performance, stealth-focused browser automation library for Python. Powered by **CDP (Chrome DevTools Protocol)** and **ADB (Android Debug Bridge)**, it allows you to scrape data from websites and native mobile apps with industry-leading anti-detection capabilities.

> **You Only Scrape Once** — data extraction made smarter, faster, and more resilient.

## Why Chuscraper?

- **🚀 Blazing Fast**: Communicates directly with the browser via CDP, skipping the heavy WebDriver overhead.
- **🥷 Stealth by Design**: Built-in mechanisms to bypass top-tier bot verification systems like Cloudflare, Akamai, and Datadome.
- **📱 Mobile Native**: First-class support for automating and extracting data from Android apps.
- **⚡ Async First**: Built on `asyncio` for high-concurrency workflows and modern performance.
- **🧩 Modular Architecture**: Mixin-based design that is powerful for experts yet simple for beginners.

## Key Capabilities

| Feature | Description |
| :--- | :--- |
| **Direct CDP** | Full control over the browser protocol without middlemen. |
| **Elite Stealth** | Automatic patching of `navigator`, `webdriver`, `WebGL`, and `Canvas`. |
| **Mobile Automation** | Control real devices or emulators for native app scraping. |
| **Universal Crawler** | High-concurrency BFS crawler with `sitemap.xml` support. |
| **Smart Locators** | CSS, XPath, and Fuzzy Text selectors that "learn" from your page. |
| **AI-Ready** | One-click conversion of content to clean **Markdown** or **Normalized Text**. |

## Quick Example

```python
import asyncio
import chuscraper as cs

async def main():
    # Start browser with elite stealth and human-like behavior
    async with await cs.start(stealth=True, headless=False) as browser:
        
        # Navigate to a protected site
        tab = await browser.get('https://example.com')
        
        # Use smart selectors to find data
        heading = await tab.find("Example Domain")
        
        # Extract data in AI-ready formats
        print(f"Heading Text: {await heading.text()}")
        print(f"Markdown Content:\n{await tab.to_markdown()}")

if __name__ == '__main__':
    asyncio.run(main())
```

---

Ready to start? Head over to the [Installation](installation.md) guide or dive into the [Quickstart](quickstart.md).
