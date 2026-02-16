# Chuscraper v0.18.0 🚀 - The "Easy Syntax" Update

This major update transforms **Chuscraper** into the most developer-friendly and intuitive web scraping framework in the Python ecosystem. We've removed boilerplate and added natural aliases for a "Zero Friction" experience.

## ✨ What's New?

### 🎮 Zero-Boilerplate Startup
You can now start a stealthy browser session directly with keyword arguments. No need to manualy create `Config` objects.
```python
browser = await zd.start(headless=False, stealth=True, proxy="...")
```

### 🔗 Intuitive Aliases & One-Liners
We've added aliases that match popular libraries like Playwright/Puppeteer and helpful one-liners for common tasks.
- **`page.goto(url)`**: Alias for `get()`.
- **`await page.title()`**: Quickly get the page title.
- **`await page.select_text(selector)`**: Get element text in a single call.

### ⚡ Browser-Level Shortcuts
Control the browser directly for simple tasks.
- **`await browser.goto(url)`**: Shortcuts the main tab navigation.
- **`await browser.scrape(selector)`**: Quickly finds an element.

### 🛡️ Hardened Navigation
- **Anti-Hang Engine**: Internal `get()` logic now includes a 15s default timeout for idle waits, preventing scripts from getting stuck on "noisy" analytics-heavy sites.

## 📦 Installation
```bash
pip install chuscraper --upgrade
```

---
*Made with ❤️ by Toufiq Qureshi*
