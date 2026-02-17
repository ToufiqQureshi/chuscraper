# Async Patterns & Concurrency

Chuscraper is built on `asyncio`. usage of `async/await` allows you to scrape multiple pages in parallel efficiently.

## Parallel Tabs

Instead of opening one tab, doing work, then opening another... do it all at once!

```python
import asyncio
import chuscraper as cs

async def scrape_url(browser, url):
    page = await browser.new_tab(url)
    try:
        title = await page.title()
        print(f"Done: {url} -> {title}")
    finally:
        await page.close()

async def main():
    urls = [
        "https://google.com",
        "https://github.com",
        "https://python.org",
        "https://example.com"
    ]
    
    async with await cs.start() as browser:
        # Create a task for each URL
        tasks = [scrape_url(browser, url) for url in urls]
        
        # Run them all concurrently
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
```

## Managing Contexts

If you need completely separate sessions (cookies, cache), create multiple contexts (incognito windows).

*Note: In the current version, `start()` creates a single profile/context. To use multiple contexts, you would launch multiple `Browser` instances or use the `Incognito` context feature if available.*

## Best Practices

1.  **Limit Concurrency**: Don't open 100 tabs at once; Chrome will crash. Use `asyncio.Semaphore`.
2.  **Error Handling**: Always wrap tab operations in `try/finally` to ensure tabs get closed.
3.  **Resource Usage**: Monitor memory. Headless browsers can be heavy.
