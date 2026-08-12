"""
Shared pytest fixtures.

Several test modules import `CreateBrowser` and use the `create_browser` /
`browser` fixtures, but this file did not exist in the repo - so those modules
failed at collection time and took the whole `tests/core` run down with them.

Browser-backed tests are opt-in via CHUSCRAPER_BROWSER_TESTS=1: they launch a
real Chrome and hit the network, so they are integration tests, not unit tests.
Without it they skip, and the pure-logic tests still run everywhere.
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator, Protocol

import pytest

import chuscraper as zd
from chuscraper.core.config import Config, find_executable


class CreateBrowser(Protocol):
    """Callable that builds a Browser with test-friendly defaults."""

    def __call__(self, **kwargs: Any) -> zd.Browser: ...

    @property
    def config(self) -> Config: ...


#: Browser-backed tests are integration tests: they launch a real Chrome and
#: several of them fetch https://example.com. On a CI runner (which ships with
#: Chrome pre-installed) they would otherwise start automatically and hang on
#: the network. Opt in explicitly instead.
BROWSER_TESTS_ENV = "CHUSCRAPER_BROWSER_TESTS"


def _browser_available() -> bool:
    if os.environ.get(BROWSER_TESTS_ENV, "").lower() not in ("1", "true", "yes"):
        return False
    try:
        find_executable("auto")
        return True
    except FileNotFoundError:
        return False


def _skip_reason() -> str:
    if os.environ.get(BROWSER_TESTS_ENV, "").lower() not in ("1", "true", "yes"):
        return f"browser-backed test; set {BROWSER_TESTS_ENV}=1 to run"
    return "no Chrome/Chromium binary available in this environment"


class _BrowserFactory:
    """Builds Browsers that are headless, sandbox-free and CI-safe."""

    def __init__(self, **defaults: Any) -> None:
        self._defaults = defaults

    def __call__(self, **kwargs: Any) -> Any:
        merged = {**self._defaults, **kwargs}
        return _BrowserContext(merged)

    @property
    def config(self) -> Config:
        return Config(**self._defaults)


class _BrowserContext:
    """Async context manager wrapping Browser.create()/stop()."""

    def __init__(self, kwargs: dict[str, Any]) -> None:
        self._kwargs = kwargs
        self._browser: zd.Browser | None = None

    @property
    def config(self) -> Config:
        """The Config these kwargs describe, without launching anything."""
        return Config(**self._kwargs)

    async def __aenter__(self) -> zd.Browser:
        self._browser = await zd.Browser.create(**self._kwargs)
        return self._browser

    async def __aexit__(self, *exc: Any) -> None:
        if self._browser is not None:
            await self._browser.stop()


@pytest.fixture
def create_browser() -> _BrowserFactory:
    """Factory for Browsers configured for tests."""
    if not _browser_available():
        pytest.skip(_skip_reason())
    return _BrowserFactory(headless=True, sandbox=False)


@pytest.fixture
async def browser() -> AsyncIterator[zd.Browser]:
    """A started, headless Browser that is stopped on teardown."""
    if not _browser_available():
        pytest.skip(_skip_reason())

    instance = await zd.Browser.create(headless=True, sandbox=False)
    try:
        yield instance
    finally:
        await instance.stop()
