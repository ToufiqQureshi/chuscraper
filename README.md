# Chuscraper 🚀

**The Undetectable & Agentic Web Scraping Framework**

`chuscraper` is a next-gen, async-first web automation library designed to bypass the toughest anti-bot protections (Akamai, Cloudflare, Datadome, etc.). Combined with **Agentic AI**, it can autonomously navigate, extract data from complex views (Vision), and heal itself from selector changes.

---

## 🔥 Key Features

### 🛡️ Undetectable Stealth Mode
- **Canvas & WebGL Noise**: Randomizes fingerprinting to avoid tracking.
- **Hardware Spoofing**: Simulates high-end PC specs (8 Cores, 8GB RAM).
- **Smart UA Rotation**: Rotates modern Desktop User-Agents per session.
- **Navigator Obfuscation**: Hides `navigator.webdriver` and mocks browser plugins.

### 🤖 Agentic AI (Powered by Gemini/OpenAI)
- **Autonomous Pilot**: Navigate websites using natural language (e.g., "Find a flight to London").
- **Multi-modal Vision**: Extract data from screenshots when HTML is messy or obfuscated.
- **Self-Healing Selectors**: AI learns robust CSS selectors that persist even after UI updates.
- **Structured Extraction**: Extract data directly into Pydantic models with 100% validation.

### 🔒 Enterprise Readiness
- **CDP-based Proxy Auth**: Support for `user:pass@host:port` without extensions.
- **Timezone Sync**: Automatically matches browser timezone to proxy location.
- **Blazing Fast**: Optimized CDP commands for high-concurrency performance.

---

## 📦 Installation

Choose the version that fits your needs:

```bash
# Core Only (Ultra Lightweight)
pip install chuscraper

# Advanced AI Suite (Pilot, Vision, Extraction)
pip install chuscraper[ai]
```

---

## 🚀 Quick Start

### 1. Autonomous Navigation (AI Pilot)
Let the AI handle the clicks and typing to reach your goal.

```python
import asyncio
from chuscraper import start

async def main():
    browser = await start(headless=False)
    page = await browser.get("https://www.makemytrip.com/")

    # AI Pilot handles the search autonomously
    await page.ai_pilot("Search for hotels in Goa for next weekend")
    
    # Extract data using Vision
    data = await page.ai_visual_extract("Extract first 3 hotel names and prices")
    print(data)

    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Stealth & Proxy (Core)
```python
browser = await chuscraper.start(
    stealth=True,
    proxy="http://user:pass@proxy.example.com:8080",
    timezone="Asia/Kolkata"
)
page = await browser.get("https://whoer.net")
print(f"Camouflage Status: {await page.title}")
```

---

## 🛠️ AI API Table

| Method | Description |
| :--- | :--- |
| `ai_pilot(goal)` | Runs an autonomous agent to achieve a natural language goal. |
| `ai_visual_extract(prompt, schema)` | Uses Vision (screenshots) to extract structured data. |
| `ai_extract(prompt, schema)` | Semantically extracts data from the page HTML. |
| `ai_learn_selector(desc)` | Learns a robust CSS/Xpath selector for an element. |

---

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
MIT License
