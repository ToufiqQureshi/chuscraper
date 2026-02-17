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

## 🕵️‍♂️ Next-Gen Stealth & Humanization (New!)
We've integrated **2026-grade** anti-fingerprinting and behavioral humanization to defeat advanced bot detection systems like CreepJS, Akamai, and Cloudflare Turnstile.

### 🛡️ Hardened Fingerprints
- **WebGPU Spoofing**: Reports high-end GPUs (e.g., "NVIDIA RTX 3060") instead of generic identifiers.
- **Worker Stealth**: Advanced `AttachedToTarget` interception prevents leaks in Web Workers and Service Workers options (fixing the "Intel" GPU leak).
- **Audio Context Jitter**: Adds micro-noise to audio processing to randomize fingerprints.

### 🤖 Behavioral Humanization (The "Sidha Function")
- **`await page.human_click(selector)`**: Moves the mouse in a natural **Bezier curve** towards the element, overshooting slightly before clicking, just like a real user.
- **`await page.human_type(selector, text)`**: Types with variable cadence and random micro-pauses to simulate human keystrokes.

## 📦 Installation
```bash
pip install chuscraper --upgrade
```

---
*Made with ❤️ by Toufiq Qureshi*
