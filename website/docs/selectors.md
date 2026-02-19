# Selectors & Locators

Finding elements reliably is the heart of automation. Chuscraper provides a smart finding engine that "guesses" what you want.

## The Smart Locator: `find`

The `find()` method is the **recommended** way to locate elements. It accepts a string and automatically tries to match it against:
1.  **Text Content** (e.g., "Login", "Welcome")
2.  **HTML Attributes** (e.g., placeholders, aria-labels)
3.  **CSS Selectors** (e.g., `.btn-primary`)

```python
# Finds the button with text "Login"
login_btn = await tab.find("Login") 

# Finds the input with placeholder "Search"
search_box = await tab.find("Search")

# Finds by CSS if it looks like one
header = await tab.find("#header")
```

### Why use `best_match=True`?
If multiple elements have similar text (e.g., "Sign In" vs "Signing In"), `best_match` picks the one closest in length to your query.

```python
btn = await tab.find("Sign In", best_match=True)
```

## CSS & XPath

If you need surgical precision, use standard selectors:

```python
# CSS Selector
el = await tab.select("div.content > p.lead")

# CSS Select all matching items
items = await tab.select_all("ul.results li")

# XPath support
el = await tab.xpath("//h1[contains(text(), 'Success')]")
```

## Waiting for Content

Always use `wait_for` to handle dynamic loading. It blocks execution until the element is ready.

```python
# Wait for a selector to appear
await tab.wait_for(".result-list")

# Wait for specific text to appear
await tab.wait_for(text="Completed Successfully")

# Custom timeout (default 10s)
await tab.wait_for("#slow-element", timeout=30)
```
