# Core Concepts

Understanding the hierarchy of objects in Chuscraper is key to mastering it.

## The Hierarchy

1.  **Browser**: The main entry point. Represents the Chrome process.
2.  **Tab**: Represents a single open tab (or page). This is where 90% of your work happens.
3.  **Element**: Represents a DOM node on the page.

## Browser

The `Browser` object manages the Chrome process and the connection to it.

```python
browser = await cs.start()
```

### Key Methods

-   `browser.tabs`: A list of all open `Tab` objects.
-   `browser.main_tab`: The currently active or first tab.
-   `browser.new_tab(url)`: Open a new tab.
-   `browser.close_tab(tab)`: Close a specific tab.
-   `browser.stop()`: Close the browser and cleanup.

## Tab

The `Tab` object is your window into a specific page. You can navigate, find elements, and execute JavaScript.

```python
tab = browser.main_tab
await tab.goto("https://google.com")
```

### Navigation

-   `await tab.goto(url)`: Navigate to a URL.
-   `await tab.wait(seconds)`: Pause execution (smart sleep).
-   `await tab.back()`: Go back in history.
-   `await tab.reload()`: Reload the page.

### Execution

-   `await tab.evaluate("document.title")`: Run JavaScript and get the result.
-   `await tab.js("console.log('hello')")`: strict alias for evaluate.

## Element

An `Element` represents a node in the HTML. You get elements by using selectors on a `Tab`.

```python
btn = await tab.select("button#submit")
await btn.click()
```

### Key Methods

-   `await element.click()`: Click the element.
-   `await element.send_keys("text")`: Type text.
-   `await element.get_attribute("href")`: Get HTML attribute.
-   `await element.text_content`: Get the inner text (property).
