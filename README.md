<p align="center">
  <img src="https://i.ibb.co/HLyG7BBK/Chat-GPT-Image-Feb-16-2026-11-13-14-AM.png" alt="Chuscraper Logo" width="180" />
</p>

<h1 align="center">🕷️ Chuscraper</h1>
<p align="center">
  <strong>Stealth-focused Web & Mobile automation framework powered by CDP and ADB</strong><br/>
  You Only Scrape Once — data extraction made smarter, faster, and more resilient.
</p>

<p align="center">
  <a href="https://pypi.org/project/chuscraper/"><img src="https://static.pepy.tech/personalized-badge/chuscraper?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads"/></a>
  <a href="https://opensource.org/licenses/AGPL-3.0"><img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg?style=for-the-badge"/></a>
  <a href="https://github.com/ToufiqQureshi/chuscraper"><img src="https://img.shields.io/badge/GitHub-Trending-blue?style=for-the-badge&logo=github"/></a>
</p>

---

## 🚀 What is Chuscraper?

Chuscraper is a Python web & mobile scraping library that uses **CDP (Chrome DevTools Protocol)** for web and **ADB (Android Debug Bridge)** for mobile apps. It extracts structured data, interacts with pages/screens, and automates workflows — with a heavy focus on **Anti-Detection** and **Stealth**.

It converts standard Chromium instances into undetectable agents that can bypass bot verification systems like Cloudflare, Akamai, and Datadome, while also allowing control of native Android apps for data extraction.

---

## 🌟 Key Features

### 📱 Native Mobile App Scraping (New!)
Chuscraper now supports scraping native Android apps using ADB:
- **UI Automation:** Tap, swipe, and type on any connected Android device (Real or Emulator).
- **XML Dumping:** Extract the full UI hierarchy as XML to find elements by text, resource-id, or content-desc.
- **Background Execution:** Run scripts without touching the device.
- **Zero-Setup:** Just enable USB Debugging and connect. No Appium server required.

### 🕵️‍♂️ Dynamic Stealth & Fingerprinting (New!)
Chuscraper now includes an advanced **Auto-Update** and **Fingerprint Rotation** engine:
- **Auto-Update Chrome Version:** Automatically detects your installed Chrome version and updates the User-Agent to match. No manual updates required!
- **Fingerprint Rotation:** Randomizes hardware fingerprints (RAM, CPU, Screen Resolution) per session while strictly adhering to your host OS (Windows, macOS, Linux) to prevent OS mismatch detection.
- **Client Hints Sync:** Automatically patches `navigator.userAgentData` to match the User-Agent string.
- **Advanced Stealth Patches:** 6 core JS bypasses for WebDriver, Chrome Runtime, Canvas/WebGL noise, and iFrame leaks.
- **Modern Timezones:** Automatically syncs browser timezone with IP location using modern IANA names.

### ⚡ Async + Fast
Built on async CDP, low overhead, no heavy browser bundles.

### 🔄 Advanced Selector & Extraction Engine (New!)
Chuscraper now includes a high-performance parsing engine:
- **Adaptive Selectors:** Save and automatically relocate elements even if the DOM structure changes.
- **AI-Ready Extraction:** One-click conversion of pages or elements to clean **Markdown** or normalized **Text**.
- **CSS & XPath Support:** Unified API for high-speed selection.

### 🔄 Flexible Outputs
Supports JSON, CSV, Markdown, Excel, Pydantic, and more.

---

## 📦 Installation

```bash
pip install chuscraper
```

> [!TIP]
> Use within a virtual environment to avoid conflicts.

---

### Example: Advanced Mode (Adaptive Stealth + Selectors)

```python
import asyncio
import chuscraper as zd
from chuscraper.core.stealth import SystemProfile

async def main():
    # Use standard Chrome via Browser.create
    async with await zd.Browser.create(proxy="http://user:pass@host:port") as browser:
        tab = await browser.get("https://www.makemytrip.com/hotels")

        # 1. Apply Industry-Leading Stealth
        profile = SystemProfile.from_system(cookie_domain="makemytrip.com")
        await profile.apply(tab)

        # 2. Use Adaptive Selectors (Resilient to DOM changes)
        # 'adaptive=True' saves the element's properties for future relocation
        hotels = await tab.select_all("h1.hotelName", adaptive=True)
        
        for hotel in hotels:
            # 3. Use AI-Ready Extraction
            print(await hotel.to_text())
            print(await hotel.to_markdown())

if __name__ == "__main__":
    asyncio.run(main())
```

> [!NOTE]
> `chuscraper` automatically handles Chrome process cleanup and Local Proxy lifecycle.

---

## ⚙️ Configuration Switches (Parameters)

Chuscraper gives you full control via `zd.start()`. Here are the powerful switches you can use:

### 🛠️ Core Switches
| Switch | Description | Default |
| :--- | :--- | :--- |
| `headless` | Run without a visible window (`True`/`False`) | `False` |
| `stealth` | **Master Switch** for advanced anti-detection (System Fingerprints + JS Bypasses) | `False` |
| `stealth_domain` | The domain used for cookie storage/loading in stealth mode | `""` |
| `user_data_dir` | Path to save/load browser profile (keep logins/cookies) | `Temp` |
| `proxy` | Proxy URL (e.g. `http://user:pass@host:port`) | `None` |

### 🚀 Advanced Switches
| Switch | Description | Default |
| :--- | :--- | :--- |
| `browser_executable_path` | Custom path to Chrome/Brave binary (auto-detect if omitted) | Auto |
| `browser` | Browser selection: `"auto"`, `"chrome"`, `"brave"` | `"auto"` |
| `browser_args` | Extra Chromium args list | `[]` |
| `sandbox` | Set `False` for Linux/Docker/root environments | `True` |
| `lang` | Browser locale/language (e.g., `en-US`, `hi-IN`) | `en-US` |
| `user_agent` | Manually override User-Agent (not recommended with `stealth=True`) | Auto |
| `disable_webrtc` | Prevent IP leaks via WebRTC | `True` |
| `disable_webgl` | Disable WebGL (can reduce detection surface in some setups) | `False` |
| `timezone` | Force timezone (IANA format, e.g. `Asia/Kolkata`) | Auto/None |
| `stealth_options` | Dict for fine-grained stealth patches | Built-in defaults |
| `retry_enabled` | Enable retry helpers for unstable workflows | `False` |
| `retry_timeout` | Retry timeout seconds | `10.0` |
| `retry_count` | Retry count | `3` |
| `browser_connection_timeout` | Wait between connection attempts | `0.25` |
| `browser_connection_max_tries` | Browser connection retries | `10` |

### 🕵️‍♂️ Granular Stealth Options
When `stealth=True`, you can fine-tune specific patches by passing a `stealth_options` dict:

```python
await zd.start(stealth=True, stealth_options={
    "patch_webdriver": True,  # Hide WebDriver
    "patch_webgl": True,      # Spoof Graphics Card
    "patch_canvas": True,     # Add Canvas Noise
    "patch_audio": False      # Disable Audio Fingerprinting noise
})
```

### 📱 Mobile Scraping Example
Scrape data from any native Android app (e.g., Hotel/Flight apps):

```python
import asyncio
from chuscraper.mobile import MobileDevice

async def main():
    # Connect to first available device
    device = await MobileDevice().connect()

    # Example: Searching for hotels
    city_input = await device.find_element(text="Enter destination")
    if city_input:
        await city_input.type("Goa")

    search_btn = await device.find_element(resource_id="com.hotel.app:id/search_btn")
    if search_btn:
        await search_btn.click()

    # Extract prices
    prices = await device.find_elements(resource_id="com.hotel.app:id/price_text")
    for price in prices:
        print(price.get_text())

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🛡️ Stealth & Anti-Detection Proof

We don't just claim to be stealthy; we prove it. Below are the results from top anti-bot detection suites, all passed with **100% "Human" status**.

👉 **[View Full Visual Proofs &amp; Screenshots Here](website/docs/stealth.md)**

| Detection Suite           | Result                   | Status  |
| ------------------------- | ------------------------ | ------- |
| **SannySoft**       | No WebDriver detected    | ✅ Pass |
| **BrowserScan**     | 100% Trust Score         | ✅ Pass |
| **PixelScan**       | Consistent Fingerprint   | ✅ Pass |
| **IPHey**           | Software Clean (Green)   | ✅ Pass |
| **CreepJS**         | 0% Stealth / 0% Headless | ✅ Pass |
| **Fingerprint.com** | No Bot Detected          | ✅ Pass |

### 🌍 Real-World Protection Bypass

We tested `chuscraper` against live websites protected by major security providers:

| Provider             | Target                  | Result                  |
| -------------------- | ----------------------- | ----------------------- |
| **Cloudflare** | Turnstile Demo          | ✅ Solved Automatically |
| **DataDome**   | Antoine Vastel Research | ✅ Accessed             |
| **Akamai**     | Nike Product Page       | ✅ Bypassed             |

---

## 📖 Documentation

Full technical guides are available in the `docs/` folder:

- [English (Main)](README.md)
- [Production Readiness](website/docs/production.md)
- [Project API Guide](docs/api_guide_v2.md)
- [Stealth Comparison](docs/stealth_comparison.md)

*Translations (Chinese, Japanese, etc.) coming soon.*

## 💖 Support & Sponsorship

`chuscraper` is an open-source project maintained by [Toufiq Qureshi]. If the library has helped you or your business, please consider supporting its development:

- **GitHub Sponsors**: [Sponsor me on GitHub](https://github.com/sponsors/ToufiqQureshi)
- **Corporate Sponsorship**: If you are a **Proxy Provider** or **Data Company**, we offer featured placement in our documentation. Contact us for partnership opportunities.
- **Custom Scraping Solutions**: Need a private, high-performance scraper? We offer professional consulting.

---

## 🛠️ Contributing

Want to contribute? Open an issue or send a pull request — all levels welcome! Please follow the `CONTRIBUTING.md` guidelines.

---

## 📜 License

Chuscraper is licensed under the **AGPL-3.0 License**. This ensures that any software using Chuscraper must also be open-source, protecting the community and your freedom.

Made with ❤️ by [Toufiq Qureshi]
