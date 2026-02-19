# Stealth & Anti-Detect

Chuscraper v0.19.3 is built to bypass modern bot protections (Cloudflare, Akamai, Datadome, etc.) out of the box with zero configuration.

## Enabling Stealth

Simply pass `stealth=True` when starting the browser.

```python
# Start in full undetected mode
browser = await cs.start(stealth=True)
```

## What's under the hood?

Our v0.19 engine applies deep patches to the browser environment before the target site can even run its first script:

1.  **Navigator Hardening**: Fixes `navigator.webdriver`, `languages`, `platform`, and `hardwareConcurrency`.
2.  **WebGL Masking**: Headless Chrome often reports a "Software Renderer" (SwiftShader). We spoof it to look like a real physical GPU (Nvidia/Intel).
3.  **Coherent Fingerprints**: Ensures that your IP, timezone, locale, and User-Agent are internally consistent and "trustworthy."
4.  **Anti-Automation Leak Fixes**: Patches properties that tools like Selenium or Puppeteer leave behind (e.g., `cdc_` string leaks).

## Testing your Browser

You can verify Chuscraper's stealth score by navigating to these benchmarks:

```python
tab = await browser.get("https://bot.sannysoft.com/")
# Check if "WebDriver" is Green (Missing) 
```

-   [CreepJS](https://abrahamjuliot.github.io/creepjs/) (Aim for high trust score)
-   [SannySoft Bot Test](https://bot.sannysoft.com/)
-   [BrowserLeaks WebGL](https://browserleaks.com/webgl)

## Headless vs Headed
While Chuscraper is extremely stealthy in **headless** mode, some sites are exceptionally aggressive. If you are getting blocked, try running with `headless=False` to see if the behavior changes.
