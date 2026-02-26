# Installation

Getting Chuscraper up and running is straightforward.

## Requirements

- **Python**: 3.10 or higher
- **Browser**: Latest Chrome/Chromium or Brave installed locally
- **OS**: Windows, macOS, or Linux

## Install via pip

```bash
pip install chuscraper
```

Or with your package manager:

```bash
uv add chuscraper
# or
poetry add chuscraper
```

## Verify installation

```python
import chuscraper as cs
print(cs.__version__)
```

## First launch (recommended baseline)

```python
import asyncio
import chuscraper as cs

async def main():
    async with await cs.start(
        stealth=True,
        production_ready=True,
        humanize=True,
        headless=False,
    ) as browser:
        tab = await browser.get("https://example.com")
        print(await tab.title())

asyncio.run(main())
```

## Optional launch switches

You can pass these directly to `cs.start(...)`:

- `stealth=True`: enable anti-detection patches
- `humanize=True`: add human-like startup motion/jitter
- `production_ready=True`: stronger retry/connect defaults
- `proxy="http://user:pass@host:port"`: route traffic via proxy
- `disable_webrtc=True`: reduce WebRTC leak surface
- `disable_webgl=False`: keep real GPU path unless your target requires disabling it
- `browser_connection_timeout` / `browser_connection_max_tries`: tune startup resilience

## Troubleshooting

### Browser not found

If auto-detection fails, pass explicit path:

```python
browser = await cs.start(
    browser_executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
)
```

### Windows event-loop issues

```python
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```
