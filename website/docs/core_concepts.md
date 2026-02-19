# Core Concepts

Chuscraper follows a clean, hierarchical structure. Each layer is enhanced with specialized **Mixins** to keep the API powerful yet easy to navigate.

## The Hierarchy

1.  **Browser**: The engine. Manages the Chrome process and global state.
2.  **Tab**: The portal. Represents a single page/tab where most automation happens.
3.  **Element**: The node. Represents specific DOM elements for interaction.

## 1. Browser

The `Browser` object is your entry point. It manages the underlying connection and coordinates tabs.

```python
# Start a browser instance
browser = await cs.start(stealth=True)
```

### Modular Attributes
Thanks to its Mixin architecture, the `Browser` object provides easy access to:
-   `browser.tabs`: List of all open `Tab` objects.
-   `browser.cookies`: Integrated `CookieJar` for session management.
-   `browser.get(url)`: Shortcut to navigate in the main tab or open a new one.

## 2. Tab

The `Tab` object is where the magic happens. It inherits from Mixins like `NavigationMixin`, `NetworkMixin`, and `ScreenshotMixin`.

```python
tab = await browser.get("https://google.com")

# New properties for easy access
print(f"I am at: {tab.url}")
```

### Key Capabilities
-   **Navigation**: `await tab.get(url)`, `await tab.back()`, `await tab.reload()`.
-   **Evaluation**: Execute JS with `await tab.evaluate("window.innerWidth")`.
-   **Waiting**: Use `await tab.wait(2)` for smart stability pauses.

## 3. Element

`Element` objects are returned by `tab.select()` or `tab.find()`. They are modularized into `State`, `Interaction`, and `Query` Mixins.

```python
btn = await tab.select("button#submit")
await btn.click()
```

### Common Actions
-   `await element.click()`: Moves mouse humanly and clicks.
-   `await element.send_keys("text")`: Types with natural delays.
-   `await element.text()`: Returns the visible text content (async).
-   `element.attrs`: Access all HTML attributes directly.
