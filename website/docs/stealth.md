# Stealth & Anti-Detection

Chuscraper is designed for modern bot-defense stacks (Cloudflare, Akamai, DataDome, etc.) with configurable stealth and behavior realism.

## Quick stealth start

```python
import asyncio
import chuscraper as cs

async def main():
    async with await cs.start(
        stealth=True,
        humanize=True,
        production_ready=True,
        headless=False,
    ) as browser:
        tab = await browser.get("https://bot.sannysoft.com/")
        await tab.wait(3)

asyncio.run(main())
```

## Elite Stealth: The Chuscraper Advantage

Unlike traditional stealth drivers, Chuscraper implements **Full-Precision Version Synchronization**.

### 1. Deep Version Sync
Most scrapers only spoof the major version (e.g., 145) in headers but leak the full kernel version via `navigator.userAgentData`. Chuscraper detects your browser's exact build and syncs it across:
- **HTTP Headers** (User-Agent)
- **Navigator Object** (Client Hints)
- **Web Workers** (Background context)

### 2. Dual-Layer CDP Patching
We use both `Network` and `Emulation` CDP domains to ensure the spoofing is consistent even for deep-probing detectors like CreepJS.

### 3. Advanced JS Bypasses
With `stealth=True`, Chuscraper injects 6+ premium bypasses:
- **WebDriver Hiding**: Removes `navigator.webdriver`.
- **Chrome Runtime Proxy**: Spoofs `window.chrome`.
- **Hardware Realism**: Randomizes RAM, CPU cores, and Screen Resolution to match your OS profile.
- **Canvas/WebGL Noise**: Prevents browser fingerprinting via graphics rendering.

## Recommended production preset

For high-friction targets:

```python
browser = await cs.start(
    stealth=True,
    humanize=True,
    production_ready=True,
    retry_enabled=True,
    retry_count=5,
    retry_timeout=20,
)
```

## Fine-grained stealth options

```python
browser = await cs.start(
    stealth=True,
    stealth_options={
        "patch_webdriver": True,
        "patch_webgl": True,
        "patch_canvas": True,
        "patch_audio": True,
        "patch_permissions": True,
        "patch_chrome_runtime": True,
    },
)
```

## Practical anti-block tips

- Prefer **residential/mobile proxies** for strict targets.
- Keep **timezone + language + proxy geolocation** aligned.
- Use `headless=False` for hardest targets.
- Reuse `user_data_dir` for persistent trust/cookies.
- Avoid rapid repetitive actions; keep realistic pacing.

## Benchmark sites

- [SannySoft](https://bot.sannysoft.com/)
- [CreepJS](https://abrahamjuliot.github.io/creepjs/)
- [BrowserLeaks WebGL](https://browserleaks.com/webgl)
