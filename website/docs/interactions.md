# Interactions

Interacting with a page in Chuscraper is built to feel natural and bypass bot detection.

## Clicking

Chuscraper doesn't just "fire" a click event; it simulates a human moving the mouse and pressing the button.

```python
btn = await tab.find("Submit")
await btn.click()
```

## Typing & Input

Typing is also humanized with slight random delays between keystrokes.

```python
search = await tab.select("input[name='q']")
await search.send_keys("best scraping library", clear=True)

# Pressing Enter
await tab.send_keys(cs.SpecialKeys.ENTER)
```

## Scrolling

Use scrolling to reveal lazy-loaded content or to look more "human."

```python
# Scroll down a bit (percentage based)
await tab.scroll_down(25)

# Scroll a specific element into view
footer = await tab.find("Terms of Service")
await footer.scroll_into_view()
```

## Navigation Properties

The `Tab` object has built-in properties to quickly check its state.

```python
print(f"Current URL: {tab.url}")
print(f"Current Title: {await tab.title()}")
```

## Screenshots & Files

```python
# Save current view
await tab.save_screenshot("debug.png")

# Full page (includes scrolling)
await tab.save_screenshot("full.png", full_page=True)

# Download a file directly
await tab.download_file("https://site.com/data.zip", "local.zip")
```

## Tab Management

```python
# Get a list of all open tabs
for t in browser.tabs:
    print(f"Tab at: {t.url}")
    if "logout" in t.url:
        await t.close()
```
