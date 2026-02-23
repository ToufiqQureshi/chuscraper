# Quickstart

Get up and running with Chuscraper in seconds.

## Installation

```sh
pip install chuscraper --upgrade
```

## Your First Script

Open a browser, navigate to a page, and extract the heading:

```python
import asyncio
import chuscraper as cs
from chuscraper.core.stealth import SystemProfile

async def main():
    # 1. Start the browser with Elite Stealth and Proxy support
    async with await cs.start(headless=False) as browser:
        
        # 2. Navigate to a URL (returns a Tab object)
        tab = await browser.get('https://example.com')
        
        # 3. Apply Elite Stealth Profile (Deep Version Sync 145)
        profile = SystemProfile.from_system(cookie_domain="example.com")
        await profile.apply(tab)
        
        # 4. Use properties easily
        print(f"Current URL: {tab.url}")
        print(f"Page Title: {await tab.title()}")

        # 5. High-Performance Selectors
        header = await tab.select("h1")
        print(f"Found heading: {await header.text()}")

if __name__ == '__main__':
    asyncio.run(main())
```

## Managing Multiple Tabs

Chuscraper makes multi-tab automation a breeze.

```python
async with await cs.start() as browser:
    # Open first tab
    tab1 = await browser.get('https://google.com')
    
    # Open another tab
    tab2 = await browser.get('https://github.com', new_tab=True)
    
    # Iterate through all open tabs
    for t in browser.tabs:
        print(f"Tab ID: {t.target_id} | URL: {t.url}")
        await t.close()
```

## Interaction Patterns

Chuscraper provides a standardized way to interact with elements.

```python
# Select an element using CSS
login_btn = await tab.select("button.login-submit")

# Click it with human-like movement
await login_btn.click()

# Type into a field
search_input = await tab.select("input[name='q']")
await search_input.send_keys("chuscraper python", clear=True)

# Press Enter
await tab.send_keys(cs.SpecialKeys.ENTER)
```

## Common Tab Methods

| Method | Description |
| :--- | :--- |
| `await tab.get(url)` | Navigate to a URL. |
| `await tab.evaluate(js)` | Execute JavaScript. |
| `await tab.save_screenshot(path)` | Save a page screenshot. |
| `await tab.wait(seconds)` | Smart wait for page stability. |
| `tab.url` | Get current URL (property). |

---

### Windows Tip
On Windows, always use the `WindowsSelectorEventLoopPolicy` for maximum stability:

```python
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```
