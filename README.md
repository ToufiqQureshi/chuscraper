🚀 **Looking for an even faster and simpler way to scrape at scale (only 5 lines of code)?** Check out our enhanced version at [**Chuscraper.com**](https://github.com/ToufiqQureshi/chuscraper)! 🚀

---

# 🕷️ Chuscraper: You Only Scrape Once

[English](README.md) | [中文](docs/chinese.md) | [日本語](docs/japanese.md) | [한국어](docs/korean.md) | [Русский](docs/russian.md) | [Türkçe](docs/turkish.md)

[![PyPI version](https://img.shields.io/pypi/v/chuscraper?style=for-the-badge&color=green)](https://pypi.org/project/chuscraper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/chuscraper?style=for-the-badge)](https://pypi.org/project/chuscraper/)
[![Clean Code](https://img.shields.io/badge/Code%20Quality-A-brightgreen?style=for-the-badge)](https://github.com/ToufiqQureshi/chuscraper)

> [!TIP]
> **Web data extraction at scale? Try Chuscraper Cloud 😉**

[Chuscraper](https://github.com/ToufiqQureshi/chuscraper) is a *web scraping* python library that uses LLM and direct CDP logic to create scraping pipelines for websites and local documents.

Just say which information you want to extract and the library will do it for you!

![Chuscraper Hero](docs/assets/logo.png)

## 🚀 Integrations
Chuscraper offers seamless integration with popular frameworks and tools to enhance your scraping capabilities. Whether you're building with Python, using LLM frameworks, or working with no-code platforms, we've got you covered.

**Integrations**:
- **LLM Frameworks**: Langchain, Llama Index, Crew.ai, Agno
- **Providers**: OpenAI, Gemini (Native), Anthropic, Ollama
- **Output**: Pydantic, JSON, CSV, Markdown

## 🚀 Quick install

The reference page for Chuscraper is available on the official page of PyPI: [pypi](https://pypi.org/project/chuscraper/).

```bash
pip install chuscraper

# IMPORTANT (for AI capabilities)
pip install chuscraper[ai]
```

**Note**: it is recommended to install the library in a virtual environment to avoid conflicts with other libraries 🐱


## 💻 Usage
There are multiple standard scraping methods that can be used to extract information from a website.

The most powerful one is the Agentic Pilot, which navigates and extracts information autonomously.

```python
import asyncio
from chuscraper import start

async def main():
    # Start the stealth browser
    browser = await start(headless=False)
    page = await browser.get("https://www.makemytrip.com/")

    # 1. Autonomous Pilot: Search for hotels
    await page.ai_pilot("Search for hotels in Goa for next week")

    # 2. Semantic Extraction
    result = await page.ai_extract("Extract hotel names and prices")
    print(result)

    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

> [!NOTE]
> For OpenAI and other models you just need to pass the provider!
> ```python
> from chuscraper.ai.providers import OpenAIProvider
> provider = OpenAIProvider(api_key="YOUR_KEY")
> await page.ai_extract("Extract data", provider=provider)
> ```

## 📖 Documentation
The documentation for Chuscraper can be found in the [docs/](docs/) folder of this repository.

## 🤝 Contributing
Feel free to contribute and join our community to discuss improvements and give us suggestions!

Please see the [contributing guidelines](CONTRIBUTING.md).

## 🔥 AI Methods

| Method Name           | Description                                                                                                      |
|-------------------------|------------------------------------------------------------------------------------------------------------------|
| ai_pilot                | Single-goal autonomous navigator that handles interaction (clicks, types) to reach a target.                    |
| ai_extract              | Semantic data extractor that converts HTML content into structured JSON/Pydantic models.                        |
| ai_visual_extract       | Multi-modal Vision scraper that extracts data directly from the rendered page screenshot.                       |
| ai_learn_selector       | Self-healing tool that generates robust CSS/Xpath selectors for long-term automation.                           |
| ai_ask                  | Context-aware Q&A that answers questions based on the current page's content.                                   |

## 🎓 Citations
If you have used our library for research purposes please quote us:
```text
  @misc{chuscraper,
    author = {Toufiq Qureshi},
    title = {Chuscraper},
    year = {2026},
    url = {https://github.com/ToufiqQureshi/chuscraper},
    note = {An undetectable & agentic python library for scraping leveraging CDP and LLMs}
  }
```

## 📜 License
Chuscraper is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

Made with ❤️ by [Toufiq Qureshi]
