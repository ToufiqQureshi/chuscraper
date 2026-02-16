<p align="center">
  <img src="https://i.ibb.co/HLyG7BBK/Chat-GPT-Image-Feb-16-2026-11-13-14-AM.png" alt="Chuscraper Logo" width="180" />
</p>

<h1 align="center">🕷️ Chuscraper</h1>
<p align="center">
  <strong>LLM + CDP powered undetectable web scraping & automation framework</strong><br/>
  You Only Scrape Once — data extraction made smarter, faster, and stealthier.
</p>

<p align="center">
  <a href="https://pypi.org/project/chuscraper/"><img src="https://static.pepy.tech/personalized-badge/chuscraper?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads"/></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge"/></a>
  <a href="https://github.com/ToufiqQureshi/chuscraper"><img src="https://img.shields.io/badge/GitHub-Trending-blue?style=for-the-badge&logo=github"/></a>
</p>

---

## 🚀 What is Chuscraper?
Chuscraper is a Python web scraping & automation library that uses **CDP (Chrome DevTools Protocol)** and **LLMs** to extract structured data, interact with pages, and automate workflows — all while staying *stealthy and undetected*.

With AI-powered extraction, you tell it *what* to extract — it figures out *how*.

---

## 🌟 Features

### 🕵️‍♂️ Stealth & Anti-Detection
- Hides `navigator.webdriver`, user agent rotation
- Canvas/WebGL noise + hardware spoofing
- Timezone & geolocation spoofing

### 🤖 AI-Driven Data Extraction
- **Semantic extraction** using LLMs
- Converts HTML into structured JSON/Pydantic

### 🧠 Autonomous Navigation
- Intelligent pilot (`ai_pilot`) that clicks/types until goal achieved

### ⚡ Async + Fast
Built on async CDP, low overhead, no heavy browser bundles.

### 🔄 Flexible Outputs
Supports JSON, CSV, Markdown, Excel, Pydantic, and more.

### 🌐 Integrations
- LLM Providers: OpenAI, Gemini, Anthropic, Ollama
- Frameworks: LangChain, LlamaIndex, Agno, Crew.ai

---

## 📦 Installation

```bash
pip install chuscraper

# For AI Capabilities
pip install chuscraper[ai]
```

> [!TIP]
> Use within a virtual environment to avoid conflicts.

---

## 💻 Quick Start (Async)

```python
import asyncio
from chuscraper import start

async def main():
    browser = await start(headless=False)
    page = await browser.get("https://www.makemytrip.com/")

    # Tell the AI what to extract
    print("AI is navigating...")
    await page.ai_pilot("Search hotels in Goa for next weekend")

    # Extract structured data
    result = await page.ai_extract("Get the first 3 hotels with prices")
    import json
    print(json.dumps(result, indent=2))

    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🤖 AI Usage with Providers
Example using **OpenAIProvider**:

```python
from chuscraper.ai.providers import OpenAIProvider

provider = OpenAIProvider(api_key="YOUR_OPENAI_API_KEY")
await page.ai_extract("Extract prices and listings", provider=provider)
```

---

## 📖 Documentation
Full docs available in the `docs/` folder:

- [English](README.md)
- [Chinese](docs/chinese.md)
- [Japanese](docs/japanese.md)
- [Korean](docs/korean.md)
- [Russian](docs/russian.md)
- [Turkish](docs/turkish.md)
- [German](docs/german.md)
- [Spanish](docs/spanish.md)
- [French](docs/french.md)
- [Portuguese](docs/portuguese.md)

---

## 🛠️ Contributing
Want to contribute? Open an issue or send a pull request — all levels welcome! Please follow the `CONTRIBUTING.md` guidelines.

---

## 📜 License
Chuscraper is licensed under the MIT License.

Made with ❤️ by [Toufiq Qureshi]
