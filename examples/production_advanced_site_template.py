"""
Production-ready template for high-friction / bot-protected websites.

What this demonstrates:
- Stealth + humanize + production-ready launch profile
- Retry with exponential backoff + jitter
- Basic block/challenge signal detection
- Proxy rotation hook (plug in your provider logic)
- Structured logging for observability

Usage:
    python examples/production_advanced_site_template.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from dataclasses import dataclass
from typing import Iterable

import chuscraper as cs


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("production-template")


@dataclass
class RunConfig:
    url: str
    max_attempts: int = 5
    base_backoff_s: float = 2.0
    max_backoff_s: float = 30.0
    headless: bool = False


async def detect_challenge_or_block(tab) -> bool:
    """Heuristic detector for common challenge/block indicators."""
    signals = await tab.evaluate(
        """
        (() => {
            const txt = (document.body?.innerText || '').toLowerCase();
            const title = (document.title || '').toLowerCase();
            const blockedKeywords = [
              'verify you are human',
              'access denied',
              'temporarily blocked',
              'captcha',
              'cf-challenge',
              'attention required'
            ];
            const matched = blockedKeywords.some(k => txt.includes(k) || title.includes(k));
            return {
              matched,
              title,
              url: location.href,
              hasTurnstile: !!document.querySelector('iframe[src*="turnstile"], .cf-turnstile')
            };
        })()
        """
    )
    logger.info("challenge-scan=%s", json.dumps(signals, ensure_ascii=False))
    return bool(signals.get("matched") or signals.get("hasTurnstile"))


def proxy_pool() -> Iterable[str | None]:
    """
    Plug your rotating proxies here.

    Example values:
      "http://user:pass@resi-proxy-1:8000"
      "http://user:pass@resi-proxy-2:8000"
    """
    yield None


async def fetch_advanced_site(cfg: RunConfig) -> dict:
    last_error: Exception | None = None
    proxies = list(proxy_pool())
    if not proxies:
        proxies = [None]

    for attempt in range(1, cfg.max_attempts + 1):
        proxy = proxies[(attempt - 1) % len(proxies)]
        logger.info("attempt=%d proxy=%s", attempt, proxy or "<none>")

        try:
            async with await cs.start(
                headless=cfg.headless,
                stealth=True,
                humanize=True,
                production_ready=True,
                proxy=proxy,
                disable_webrtc=True,
                disable_webgl=False,
                retry_enabled=True,
                retry_count=5,
                retry_timeout=20.0,
                browser_connection_timeout=0.5,
                browser_connection_max_tries=20,
                lang="en-US",
                # optional, tune if needed:
                stealth_options={
                    "patch_webdriver": True,
                    "patch_canvas": True,
                    "patch_audio": True,
                    "patch_webgl": True,
                    "patch_permissions": True,
                    "patch_chrome_runtime": True,
                },
            ) as browser:
                tab = await browser.get(cfg.url)
                await tab.wait(4)

                blocked = await detect_challenge_or_block(tab)
                if blocked:
                    raise RuntimeError("challenge_or_block_detected")

                title = await tab.title()
                html = await tab.get_content()

                logger.info("success title=%s html_size=%d", title, len(html))
                return {
                    "ok": True,
                    "attempt": attempt,
                    "title": title,
                    "html_size": len(html),
                    "url": cfg.url,
                }

        except Exception as exc:  # intentional: production retry boundary
            last_error = exc
            backoff = min(cfg.max_backoff_s, cfg.base_backoff_s * (2 ** (attempt - 1)))
            jitter = random.uniform(0.0, 1.5)
            sleep_s = backoff + jitter
            logger.warning(
                "attempt=%d failed error=%s next_retry_in=%.2fs",
                attempt,
                repr(exc),
                sleep_s,
            )
            await asyncio.sleep(sleep_s)

    raise RuntimeError(f"all_attempts_failed last_error={last_error!r}")


async def main() -> None:
    cfg = RunConfig(
        url="https://example.com",
        max_attempts=4,
        headless=False,
    )
    result = await fetch_advanced_site(cfg)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
