# Interactions

Once you have an `Element` or a `Tab`, you want to interact with it.

## Clicking

```python
btn = await tab.find("Submit")
await btn.click()
```

### Advanced Clicking
You can simulate specific mouse events if `click()` is detected or blocked.
```python
# Mouse move and click
await tab.mouse_click(x=100, y=200)

# Right click
await tab.mouse_click(100, 200, button="right")
```

## Typing & Input

To type into an input field:

```python
inp = await tab.select("input#search")
await inp.send_keys("Hello World")
```

### Special Keys
To press Enter, Tab, etc., use the keys directly (newline often works for Enter in `send_keys`):

```python
# Type and press Enter
await inp.send_keys("Search Query\n")
```

## Scrolling

Chuscraper has built-in smooth scrolling to simulate human behavior.

```python
# Scroll down 25% of the page
await tab.scroll_down(amount=25)

# Scroll to specific element
el = await tab.find("Footer Link")
await el.scroll_into_view()
```

## Screenshots

You can take screenshots of the specific element or the whole page.

```python
# Element screenshot
btn = await tab.select("#chart")
await btn.save_screenshot("chart.png")

# Page screenshot
await tab.save_screenshot("full_page.png")
await tab.save_screenshot("full_page_scrolled.png", full_page=True)
```

## Downloading Files
Chuscraper handles downloads automatically if you set a download path, or you can use `download_file`.

```python
# Manual download
await tab.download_file("https://example.com/report.pdf", "my_report.pdf")
```
