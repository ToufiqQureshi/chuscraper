---
sidebar_position: 5
---

# Production Readiness

This guide focuses on stable, long-running scraping/automation workloads.

## Production checklist

1. Pin version in your `requirements.txt`
2. Use `async with` lifecycle for guaranteed cleanup
3. Enable `production_ready=True` for safer connection/retry behavior
4. Enable `stealth=True` for protected sites
5. Add `humanize=True` when facing behavioral bot checks
6. Use robust proxy rotation and backoff strategy

## Hardened launch template

```python
import asyncio
import chuscraper as cs

async def run_job(url: str):
    async with await cs.start(
        headless=True,
        stealth=True,
        humanize=True,
        production_ready=True,
        retry_enabled=True,
        retry_count=5,
        retry_timeout=20.0,
        browser_connection_timeout=0.5,
        browser_connection_max_tries=20,
        disable_webrtc=True,
    ) as browser:
        tab = await browser.get(url)
        await tab.wait(2)
        return await tab.title()


async def main():
    title = await run_job("https://example.com")
    print(title)


if __name__ == "__main__":
    asyncio.run(main())
```


## Ready-to-use example in repo

Use this advanced template directly and customize proxy/challenge logic:

- `examples/production_advanced_site_template.py`

## Failure handling strategy

- Wrap navigation and extraction in retry blocks.
- Log URL, proxy, status code, and exception details.
- On repeated block pages, rotate identity (`proxy`, optionally profile).
- Keep per-target throttling to avoid burst fingerprints.

## Performance notes

- `headless=True` is generally faster.
- `headless=False` may perform better for very strict anti-bot pages.
- Disable unnecessary resources with request interception if your workflow allows.

## Observability suggestions

- Persist structured logs for each run.
- Track block/challenge rate and success rate by domain.
- Keep a canary target (known easy page) to separate infra failures from target-site blocking.
