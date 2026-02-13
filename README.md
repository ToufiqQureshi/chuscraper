# Chuscraper 🚀

**The Undetectable Web Scraping Framework**

`chuscraper` is a powerful, async-first web automation library designed to bypass the toughest anti-bot protections (Akamai, Cloudflare, Datadome, etc.). It is built on top of the Chrome DevTools Protocol (CDP) and includes advanced stealth techniques out-of-the-box.

---

## 🔥 Key Features

- **🛡️ Undetectable Stealth Mode**:
  - Automatically hides `navigator.webdriver`.
  - Mocks `navigator.permissions`, `navigator.plugins`, and `navigator.mimeTypes`.
  - **Pro Features**:
    - **Canvas & WebGL Noise**: Randomizes fingerprinting to avoid tracking.
    - **Hardware Spoofing**: Simulates high-end PC specs (8 Cores, 8GB RAM).
    - **Smart UA Rotation**: Rotates modern Desktop User-Agents per session.

- **🔒 Built-in Proxy Auth**:
  - Direct CDP-based proxy authentication (no extensions required).
  - Supports `http://user:pass@host:port` format seamlessly.
  - Bypasses proxy authentication popups automatically.

- **🌍 Timezone & Geolocation**:
  - Automatically overrides system timezone to match your proxy (e.g., `Asia/Kolkata`).

- **⚡ Blazing Fast**:
  - Uses specific CDP commands to avoid bloat.
  - Lightweight and optimized for high-concurrency scraping.

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/ToufiqQureshi/chuscraper.git
cd chuscraper

# Install dependencies (if any specific ones, otherwise uses standard libs)
pip install -e .
```

## 🚀 Quick Start

### 1. Basic Usage (Stealth + Proxy)

```python
import asyncio
import chuscraper

async def main():
    # Start browser with Stealth Mode and Proxy
    browser = await chuscraper.start(
        stealth=True,
        proxy="http://user:pass@proxy.example.com:8080",
        timezone="Asia/Kolkata"  # Match your proxy location
    )

    page = await browser.get("https://whoer.net")
    
    # Verify IP and camouflage
    print(f"Title: {await page.title}")
    
    await asyncio.sleep(10)
    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🛠️ Configuration

| Argument | Type | Description |
| :--- | :--- | :--- |
| `stealth` | `bool` | Enable advanced anti-detection (Canvas noise, Hardware mocks, UA rotation). |
| `proxy` | `str` | Proxy URL in `scheme://user:pass@host:port` format. |
| `timezone` | `str` | Override browser timezone (e.g., `"Asia/Kolkata"`). |
| `headless` | `bool` | Run in headless mode (default: `False`). |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License
