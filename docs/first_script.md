# Your First Scraper

Let's build a simple script to scrape a website. We'll use `https://example.com` for this tutorial.

## The Basic Structure

Chuscraper is an **async** library, so we need to run our code inside an `async def` function and execute it with `asyncio.run()`.

### 1. Import and Setup

```python
import asyncio
import chuscraper as cs

async def main():
    # Start the browser
    # logic: headless=False ensures we can see the browser open.
    browser = await cs.start(headless=False)
    
    # ... your code here ...

    # Always stop the browser when done
    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Context Manager (Recommended)

To handle cleanup automatically (even if errors occur), use `async with`:

```python
async def main():
    async with await cs.start(headless=False) as browser:
        # Browser closes automatically after this block
        pass
```

### 3. Navigating and Extracting

Now let's go to a page and get some data.

```python
import asyncio
import chuscraper as cs

async def main():
    async with await cs.start(headless=False) as browser:
        # Access the main tab (the first open tab)
        tab = browser.main_tab
        
        print("Navigating...")
        await tab.goto("https://example.com")
        
        # Get the title
        title = await tab.title()
        print(f"Page Title: {title}")
        
        # Get text from an element using CSS selector
        # 'p' selects the paragraph tag
        content = await tab.select_text("p")
        print(f"Content: {content}")
        
        # Wait a bit just to see the result
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
```

## What happened?

1.  `cs.start(headless=False)` launched a new Chrome instance.
2.  `browser.main_tab` gave us control over the first tab.
3.  `tab.goto(...)` navigated to the URL.
4.  `tab.select_text("p")` found the first `<p>` element and returned its text content.

## Next Steps

Now that you have a running browser, learn about:

- [Core Concepts](core_concepts.md) (Understanding Tabs and Browsers)
- [Selectors](selectors.md) (How to find specific elements)
