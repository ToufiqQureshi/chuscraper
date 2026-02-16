<p align="center">
  <img src="https://i.ibb.co/HLyG7BBK/Chat-GPT-Image-Feb-16-2026-11-13-14-AM.png" alt="Chuscraper Logo" width="180" />
</p>

<h1 align="center">🕷️ Chuscraper</h1>
<p align="center">
  <strong>LLM + CDP powered stealth-focused web scraping & automation framework</strong><br/>
  You Only Scrape Once — data extraction made smarter, faster, and more resilient.
</p>

<p align="center">
  <a href="https://pypi.org/project/chuscraper/"><img src="https://static.pepy.tech/personalized-badge/chuscraper?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads"/></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge"/></a>
  <a href="https://github.com/ToufiqQureshi/chuscraper"><img src="https://img.shields.io/badge/GitHub-Trending-blue?style=for-the-badge&logo=github"/></a>
</p>

---

## 🚀 What is Chuscraper?
Chuscraper is a Python web scraping & automation library that uses **CDP (Chrome DevTools Protocol)** and **LLMs** to extract structured data, interact with pages, and automate workflows — with a heavy focus on **Anti-Detection** and **Stealth**.

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

---

## 💻 Quick Start (The "Easy" Way)

Chuscraper is designed for **Zero Boilerplate**. You don't need complex configuration objects just to start a stealthy session.

```python
import asyncio
import chuscraper as zd

async def main():
    # DIRECT START: Specify stealth, proxy, or headless directly in start()
    async with await zd.start(headless=False, stealth=True) as browser:
        
        # 🟢 BROWSER-LEVEL SHORTCUT
        await browser.goto("https://www.makemytrip.com/")
        
        # 🟢 INTUITIVE ALIASES (goto, title, select_text)
        page = browser.main_tab
        await page.goto("https://example.com")
        
        title = await page.title()
        header = await page.select_text("h1")
        
        print(f"Bhai, Title hai: {title}")
        print(f"Header: {header}")

        # 🤖 AI-POWERED PILOT
        print("AI is navigating...")
        await page.ai_pilot("Search hotels in Goa for next weekend")

        # EXTRACT structured data
        result = await page.ai_extract("Get the first 3 hotels with prices")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

> [!NOTE]
> `chuscraper` automatically handles Chrome process cleanup and Local Proxy lifecycle.

---

## 🤖 AI Usage with Providers
Chuscraper supports multiple providers out-of-the-box.

### 1. Gemini (Native)
```python
from chuscraper.ai.providers import GeminiProvider
provider = GeminiProvider(api_key="YOUR_GEMINI_API_KEY")
await page.ai_extract("Extract data", provider=provider)
```

### 2. OpenAI
```python
from chuscraper.ai.providers import OpenAIProvider
provider = OpenAIProvider(api_key="YOUR_OPENAI_API_KEY")
await page.ai_extract("Extract data", provider=provider)
```


## 🛡️ Stealth & Anti-Detection Proof

We don't just claim to be stealthy; we prove it. Below are the results from top anti-bot detection suites, all passed with **100% "Human" status**.

👉 **[View Full Visual Proofs & Screenshots Here](docs/STEALTH_PROOF.md)**

| Detection Suite | Result | Status |
|----------------|--------|--------|
| **SannySoft** | No WebDriver detected | ✅ Pass |
| **BrowserScan** | 100% Trust Score | ✅ Pass |
| **PixelScan** | Consistent Fingerprint | ✅ Pass |
| **IPHey** | Software Clean (Green) | ✅ Pass |
| **CreepJS** | 0% Stealth / 0% Headless | ✅ Pass |
| **Fingerprint.com** | No Bot Detected | ✅ Pass |

### 🌍 Real-World Protection Bypass
We tested `chuscraper` against live websites protected by major security providers:

| Provider | Target | Result |
|----------|--------|--------|
| **Cloudflare** | Turnstile Demo | ✅ Solved Automatically |
| **DataDome** | Antoine Vastel Research | ✅ Accessed |
| **Akamai** | Nike Product Page | ✅ Bypassed |

---

## 📖 Documentation
Full technical guides are available in the `docs/` folder:

- [English (Main)](README.md)
- [Project API Guide](docs/api_guide_v2.md)
- [Stealth Comparison](docs/stealth_comparison.md)

*Translations (Chinese, Japanese, etc.) coming soon.*

---

## 🛠️ Contributing
Want to contribute? Open an issue or send a pull request — all levels welcome! Please follow the `CONTRIBUTING.md` guidelines.

---

## 📜 License
Chuscraper is licensed under the MIT License.

Made with ❤️ by [Toufiq Qureshi]
