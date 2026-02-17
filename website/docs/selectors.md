# Selectors & Locators

Finding elements reliably is the most important part of scraping. Chuscraper provides a versatile finding engine.

## The `find` vs `select` Philosophy

-   **`select(selector)`**: strictly expects a CSS selector. Returns the *first* match.
-   **`select_all(selector)`**: Returns *all* matches as a list.
-   **`find(text_or_selector)`**: The **smart** locator. It tries to guess if you mean text or CSS.

## Smart Finding (`find`)

The `find` method is unique to Chuscraper. It accepts a string and tries to match it against:
1.  CSS Selectors
2.  Text Content (exact or partial)
3.  Attributes (like placeholder, title)

```python
# Finds by text "Login"
btn = await tab.find("Login") 

# Finds by partial text if unique
btn = await tab.find("Log") 

# Finds by CSS if it looks like CSS
btn = await tab.find(".login-btn")
```

### `best_match=True`

When searching by text, websites often have multiple elements with similar text (e.g. "Login" in header and footer). `best_match=True` uses heuristics (like text length closeness) to pick the most likely candidate.

```python
# Webpage has "Login Now" and "Login to your account"
# This will pick "Login Now" because it's closer in length to "Login"
btn = await tab.find("Login", best_match=True)
```

## CSS Selectors (`select`)

Standard CSS selectors. Fast and precise.

```python
# ID
await tab.select("#main")

# Class
await tab.select(".nav-item")

# Attribute
await tab.select("input[name='email']")

# Hierarchy
await tab.select("div.content > p")
```

## Waiting for Elements

Don't use `time.sleep()`. Use `wait_for` to wait until an element appears in the DOM.

```python
# Blocks until the element appears or timeout (default 10s)
el = await tab.wait_for(".dynamic-content")

# Wait for text to appear
el = await tab.wait_for(text="Submission Successful")
```

### Timeout

You can customize the timeout:

```python
try:
    el = await tab.wait_for("#slow-loader", timeout=30)
except asyncio.TimeoutError:
    print("Element didn't appear!")
```
