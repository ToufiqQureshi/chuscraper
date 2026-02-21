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

## What stealth mode applies

With `stealth=True`, Chuscraper applies:

1. **WebDriver hardening** (`navigator.webdriver` masking)
2. **Client hints + UA coherence**
3. **WebGL and hardware profile spoofing**
4. **Chrome runtime + permissions noise reduction**
5. **Device metrics and locale/timezone coherence**

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
