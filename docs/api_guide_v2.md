# Chuscraper: Developer Guide (Patchright Ecosystem Edition)

`chuscraper` is a high-performance, stealth-focused browser automation library for Python, built on top of Chrome DevTools Protocol (CDP).
It has been upgraded with the **Patchright Architecture**, featuring a **Local Proxy Forwarder** for bulletproof IP masking and **Advanced Stealth** to bypass bot detection.

---

## 🚀 Quick Start

### 1. Installation
Ensure you have Python 3.10+ and Google Chrome installed.
```bash
pip install chuscraper
```

### 2. Basic Scraping (The "Patchright Way")
This example demonstrates the new **Local Proxy** and **Stealth** features.

```python
import asyncio
from chuscraper import start

async def main():
    # START BROWSER with Proxy & Stealth
    # - proxy: triggers LocalAuthProxy (No popups, 100% masking)
    # - stealth: patches navigator.webdriver, mock chrome props, etc.
    browser = await start(
        proxy="http://user:pass@host:port",
        stealth=True,        # enable anti-detection
        headless=False,      # see what's happening
        timezone="Asia/Kolkata" # optional: match proxy timezone
    )

    # OPEN NEW TAB
    # Uses robust target creation logic
    page = await browser.get("https://whoer.net", new_tab=True)

    # WAIT for content
    await page.wait(5)

    # INTERACT
    # robust selectors that wait for element to appear
    await page.type('input[name="search"]', "Hello World")
    await page.click('#submit-button')
    
    # EXTRACT DATA
    # .find() waits for element and returns it
    element = await page.select("h1.title")
    print(f"Title: {element.text}")

    # SCREENSHOT
    await page.save_screenshot("proof.png")

    # CLEANUP
    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📚 Core API Reference

### 1. `chuscraper.start(**kwargs)`
The entry point. Spawns a Chrome process.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `proxy` | `str` | Proxy URL (`http://user:pass...`). **Auto-starts Local Proxy.** |
| `stealth` | `bool` | Enable anti-detection patches (Webdriver, WebGL, etc.). |
| `headless` | `bool` | Run without UI. Default `False`. |
| `user_data_dir` | `path` | Path to persistent profile. |
| `browser_args` | `list` | Custom flags (e.g., `["--start-maximized"]`). |

### 2. `Browser` Object
Manage the browser session.

| Method | Description |
| :--- | :--- |
| `await get(url, new_tab=True)` | Navigate to URL. Best way to open tabs. |
| `await stop()` | Close browser and stop Local Proxy. |
| `tabs` | List of active `Tab` objects. |

### 3. `Tab` Object
Represents a page/tab. Most work happens here.

**Navigation & Waiting**
- `await get(url)`: Navigate current tab.
- `await wait(seconds)`: Sleep (async).
- `await reload()`: Refresh page.

**Finding Elements**
- `await select(selector, timeout=10)`: Find element by CSS selector (waits until found).
- `await find(text, timeout=10)`: Find element by visible text.
- `await query_selector_all(selector)`: Get all matching elements.

**Interaction**
- `await evaluate(js_code)`: Execute JavaScript. Returns result.
- `await save_screenshot(filename)`: Capture page.
- `await close()`: Close tab.

### 4. `Element` Object
Represents a DOM node.

| Method | Description |
| :--- | :--- |
| `await click()` | Click the element. |
| `await type(text)` | Type text into input. |
| `text` | Property: Get visible text. |
| `attributes` | Property: Get all attributes. |
| `await send_keys(text)` | Low-level keystroke simulation. |

---

## 🛡️ Anti-Detection Features (Built-in)

You don't need external plugins. Just set `stealth=True`.

1.  **Local Auth Proxy:** 
    - Instead of sending credentials to Chrome (which causes popups), `chuscraper` starts a local TCP server. 
    - Validates upstream, injects headers, and forwards traffic. 
    - Chrome only sees `127.0.0.1`.
2.  **WebDriver Patch:** 
    - `navigator.webdriver` is set to `undefined` (not present).
3.  **Chrome Runtime Mock:** 
    - Mocks `window.chrome` to look like a regular user.
4.  **Hardware Concurrency:** 
    - Spoofs CPU cores to avoid fingerprinting.
5.  **Timezone Override:** 
    - Matches browser timezone to your proxy IP (optional via `timezone` arg).

---

## 🛠️ Best Practices

1.  **Use `browser.get(url, new_tab=True)`:**
    - Safest way to create pages. Handles race conditions automatically.
2.  **Prefer `select()` over `query_selector()`:**
    - `select()` waits for the element to appear (auto-wait), reducing flakiness.
3.  **Use `evaluate()` for scraping:**
    - For bulk data extraction, running JS inside the page is often faster and more reliable than fetching individual elements.
    ```python
    data = await page.evaluate("() => { return document.title; }")
    ```
4.  **Error Handling:**
    - Always use `try...finally` to ensure `browser.stop()` is called, otherwise orphaned Chrome processes may remain.

---

## 🧩 Advanced: Custom Scripts
Inject scripts before page load (useful for bypassing specific checks).

```python
await page.send(cdp.page.add_script_to_evaluate_on_new_document(
    source="Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});"
))
```
