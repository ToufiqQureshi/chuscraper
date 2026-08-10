"""
Regression tests for the bug sweep.

These deliberately avoid launching a browser: every case here is a pure-logic
bug that was shipping to production, and each one must stay cheap enough to run
in CI on every commit.
"""

import asyncio
import json
import subprocess
import shutil
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BYPASS_DIR = REPO_ROOT / "chuscraper" / "engine" / "bypasses"


# --------------------------------------------------------------------------
# JS bypass scripts
# --------------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("js_file", sorted(BYPASS_DIR.glob("*.js")), ids=lambda p: p.name)
def test_bypass_scripts_are_valid_javascript(js_file):
    """
    Every bypass must parse.

    webdriver_fully.js shipped with `function get webdriver()`, which is a
    syntax error. A parse failure in an injected script is silent, so
    navigator.webdriver stayed true in every session and - because all the
    bypasses were concatenated into one script - it took every other bypass
    down with it.
    """
    result = subprocess.run(
        ["node", "--check", str(js_file)], capture_output=True, text=True
    )
    assert result.returncode == 0, f"{js_file.name} is not valid JS:\n{result.stderr}"


def test_all_declared_bypass_files_exist():
    """BYPASS_FILES must not reference scripts that aren't shipped."""
    from chuscraper.core.stealth import BYPASS_FILES, BYPASS_TOGGLES

    for name in BYPASS_FILES:
        assert (BYPASS_DIR / name).is_file(), f"{name} is declared but missing"
        assert name in BYPASS_TOGGLES, f"{name} has no stealth_options toggle"


# --------------------------------------------------------------------------
# RateLimiter
# --------------------------------------------------------------------------

async def test_rate_limiter_survives_hitting_the_limit():
    """
    `self._lock.acquire()` was called without `await`, so the lock was never
    re-acquired and the enclosing `async with` blew up on release:
    RuntimeError: Lock is not acquired.
    """
    from chuscraper.core.limiter import RateLimiter

    limiter = RateLimiter(max_requests=2, time_window=1)
    for _ in range(4):
        await limiter.acquire()  # 3rd call trips the limit branch

    assert len(limiter.requests) <= limiter.max_requests


async def test_rate_limiter_actually_throttles():
    from chuscraper.core.limiter import RateLimiter

    limiter = RateLimiter(max_requests=2, time_window=1)
    loop = asyncio.get_running_loop()
    started = loop.time()
    for _ in range(3):
        await limiter.acquire()
    # the 3rd acquire must have waited for the window to roll over
    assert loop.time() - started >= 0.9


async def test_rate_limiter_is_safe_under_concurrency():
    from chuscraper.core.limiter import RateLimiter

    limiter = RateLimiter(max_requests=3, time_window=1)
    await asyncio.gather(*(limiter.acquire() for _ in range(6)))


# --------------------------------------------------------------------------
# util.filter_recurse_all
# --------------------------------------------------------------------------

class _FakeNode:
    def __init__(self, children=None, shadow_roots=None, backend_node_id=1):
        self.children = children or []
        self.shadow_roots = shadow_roots
        self.backend_node_id = backend_node_id


def test_filter_recurse_all_handles_empty_shadow_roots():
    """
    Chrome sends `[]` (not None) for a node with no shadow roots. The guard was
    `is not None`, so `shadow_roots[0]` raised IndexError on ordinary pages.
    """
    from chuscraper.core.util import filter_recurse_all

    tree = _FakeNode(children=[_FakeNode(shadow_roots=[])])
    assert filter_recurse_all(tree, lambda n: False) == []


def test_filter_recurse_all_walks_every_shadow_root():
    from chuscraper.core.util import filter_recurse_all

    target = _FakeNode(backend_node_id=99)
    # target lives in the *second* shadow root; only [0] used to be searched
    host = _FakeNode(shadow_roots=[_FakeNode(), _FakeNode(children=[target])])
    tree = _FakeNode(children=[host])

    found = filter_recurse_all(tree, lambda n: n.backend_node_id == 99)
    assert target in found


def test_filter_recurse_handles_empty_shadow_roots():
    from chuscraper.core.util import filter_recurse

    tree = _FakeNode(children=[_FakeNode(shadow_roots=[])])
    assert filter_recurse(tree, lambda n: False) is None


# --------------------------------------------------------------------------
# Crawler
# --------------------------------------------------------------------------

async def test_crawler_sync_callback_is_not_dropped():
    """
    A non-async `on_page_crawled` hit a bare `pass`: the page was neither passed
    to the callback nor stored in results. Silent, total data loss.
    """
    from chuscraper.spider.core import Crawler

    seen = []
    crawler = Crawler(start_urls="https://example.com", on_page_crawled=seen.append)
    await crawler._emit({"url": "https://example.com", "markdown": "hi"})

    assert seen == [{"url": "https://example.com", "markdown": "hi"}]


async def test_crawler_async_callback_still_works():
    from chuscraper.spider.core import Crawler

    seen = []

    async def cb(data):
        seen.append(data)

    crawler = Crawler(start_urls="https://example.com", on_page_crawled=cb)
    await crawler._emit({"url": "u"})
    assert seen == [{"url": "u"}]


async def test_crawler_without_callback_stores_results():
    from chuscraper.spider.core import Crawler

    crawler = Crawler(start_urls="https://example.com")
    await crawler._emit({"url": "u"})
    assert crawler.results == [{"url": "u"}]


async def test_crawler_respects_max_pages_under_concurrency():
    """N workers each passed the budget check before any of them recorded a
    visit, so max_pages could be overshot by up to N."""
    from chuscraper.spider.core import Crawler

    crawler = Crawler(start_urls="https://example.com", max_pages=3)
    claims = await asyncio.gather(
        *(crawler._claim(f"https://example.com/{i}") for i in range(10))
    )
    assert sum(claims) == 3


async def test_crawler_claim_is_idempotent():
    from chuscraper.spider.core import Crawler

    crawler = Crawler(start_urls="https://example.com", max_pages=10)
    assert await crawler._claim("https://example.com/a") is True
    assert await crawler._claim("https://example.com/a") is False


def test_crawler_formats_default_is_not_shared():
    """`formats: List[str] = ["markdown"]` was a mutable default argument."""
    from chuscraper.spider.core import Crawler

    a = Crawler(start_urls="https://example.com")
    b = Crawler(start_urls="https://example.com")
    a.formats.append("html")
    assert b.formats == ["markdown"]


# --------------------------------------------------------------------------
# Markdown extraction
# --------------------------------------------------------------------------

def test_markdown_keeps_image_only_containers():
    """
    The "remove empty elements" pass deleted any element with no text, which
    took out `<div><img></div>`, image links and figures - images included.
    """
    from chuscraper.extractors.markdown import html_to_markdown

    html = '<html><body><div><img src="/cat.png" alt="a cat"></div></body></html>'
    assert "cat.png" in html_to_markdown(html)


def test_markdown_keeps_every_article():
    """`soup.find('article')` returned only the first card on listing pages."""
    from chuscraper.extractors.markdown import html_to_markdown

    html = """<html><body>
        <article><h2>First post</h2><p>one</p></article>
        <article><h2>Second post</h2><p>two</p></article>
        <article><h2>Third post</h2><p>three</p></article>
    </body></html>"""
    out = html_to_markdown(html)
    assert "First post" in out
    assert "Second post" in out
    assert "Third post" in out


def test_markdown_drops_genuinely_empty_elements():
    from chuscraper.extractors.markdown import html_to_markdown

    html = "<html><body><div></div><p>real text</p></body></html>"
    assert "real text" in html_to_markdown(html)


def test_markdown_raises_instead_of_returning_error_text():
    """
    On failure it returned "Error converting to markdown: ..." *as the page
    content*, so the error string landed in crawler output as a real document.
    """
    from chuscraper.extractors.markdown import MarkdownConverter, MarkdownConversionError

    converter = MarkdownConverter()
    converter._new_h2t = lambda: (_ for _ in ()).throw(RuntimeError("boom"))

    with pytest.raises(MarkdownConversionError):
        converter.convert("<html><body><p>x</p></body></html>")


# --------------------------------------------------------------------------
# Mobile / ADB
# --------------------------------------------------------------------------

async def test_adb_input_text_escapes_shell_metacharacters(monkeypatch):
    """
    `adb shell` joins its args into a device-side shell command, so unescaped
    text was arbitrary command execution on the device.
    """
    from chuscraper.mobile.device import MobileDevice

    sent = {}

    async def fake_cmd(self, *args, timeout=10.0):
        sent["args"] = args
        return ""

    monkeypatch.setattr(MobileDevice, "_adb_cmd", fake_cmd)

    device = MobileDevice(serial="test")
    await device.input_text("hi'; rm -rf /data; echo '")

    payload = sent["args"][-1]

    # The whole argument must be one single-quoted shell literal, so the
    # device's shell cannot see `;` as a command separator.
    assert payload.startswith("'") and payload.endswith("'")

    # Every embedded quote must be neutralised as the '\'' escape sequence,
    # i.e. no bare ' survives that could close the literal early.
    body = payload[1:-1]
    assert "'" not in body.replace("'\\''", "")


async def test_adb_input_text_encodes_spaces_and_percent(monkeypatch):
    from chuscraper.mobile.device import MobileDevice

    sent = {}

    async def fake_cmd(self, *args, timeout=10.0):
        sent["args"] = args
        return ""

    monkeypatch.setattr(MobileDevice, "_adb_cmd", fake_cmd)

    device = MobileDevice(serial="test")
    await device.input_text("50% off now")

    payload = sent["args"][-1]
    assert "%%" in payload          # literal % escaped
    assert "%s" in payload          # spaces encoded


async def test_adb_input_text_rejects_non_string(monkeypatch):
    from chuscraper.mobile.device import MobileDevice

    device = MobileDevice(serial="test")
    with pytest.raises(TypeError):
        await device.input_text(1234)


class _FakeTag:
    name = "node"

    def __init__(self, attrs):
        self._attrs = attrs

    def get(self, key, default=None):
        return self._attrs.get(key, default)


async def test_mobile_element_click_reports_bad_bounds():
    """Bare `except: pass` made a click that did nothing look like success."""
    from chuscraper.mobile.element import MobileElement

    element = MobileElement(device=None, tag=_FakeTag({"bounds": "not-a-bounds"}))
    with pytest.raises(ValueError):
        await element.click()


async def test_mobile_element_click_reports_missing_bounds():
    from chuscraper.mobile.element import MobileElement

    element = MobileElement(device=None, tag=_FakeTag({}))
    with pytest.raises(ValueError):
        await element.click()


async def test_mobile_element_click_taps_centre():
    from chuscraper.mobile.element import MobileElement

    taps = []

    class FakeDevice:
        async def tap(self, x, y):
            taps.append((x, y))

    element = MobileElement(FakeDevice(), _FakeTag({"bounds": "[100,200][300,400]"}))
    await element.click()
    assert taps == [(200, 300)]


# --------------------------------------------------------------------------
# Position geometry
# --------------------------------------------------------------------------

def test_position_bounding_box_for_rotated_quad():
    """
    The old tuple unpack listed each name twice, so it silently kept corners
    3 and 4 - fine for axis-aligned boxes, wrong for transformed elements.
    """
    from chuscraper.core.elements.interaction import Position

    # a quad rotated 45 degrees around (100, 100)
    pos = Position([100, 80, 120, 100, 100, 120, 80, 100])
    assert (pos.left, pos.right) == (80, 120)
    assert (pos.top, pos.bottom) == (80, 120)
    assert pos.center == (100, 100)


def test_position_axis_aligned_still_correct():
    from chuscraper.core.elements.interaction import Position

    pos = Position([10, 20, 110, 20, 110, 70, 10, 70])
    assert (pos.left, pos.top, pos.right, pos.bottom) == (10, 20, 110, 70)
    assert (pos.width, pos.height) == (100, 50)


# --------------------------------------------------------------------------
# Stealth
# --------------------------------------------------------------------------

def test_host_platform_matches_the_real_os():
    """Reporting Windows on Linux contradicts the UA and every un-spoofable
    signal - it's a detection tell, not a bypass."""
    from chuscraper.core.stealth import host_platform

    ua_platform, version, arch, nav_platform = host_platform()

    expected = {"linux": "Linux", "darwin": "macOS", "win32": "Windows"}
    for prefix, name in expected.items():
        if sys.platform.startswith(prefix):
            assert ua_platform == name
            break
    assert version and arch in ("x86", "arm")
    assert nav_platform


def test_stealth_viewport_is_smaller_than_screen():
    """window.outerHeight === window.innerHeight is a classic headless tell."""
    from chuscraper.core.stealth import SystemProfile

    profile = SystemProfile(screen_width=1920, screen_height=1080, user_agent="x", _fingerprint={"a": 1})
    assert profile.viewport_height < profile.screen_height


def test_stealth_script_escapes_user_agent():
    """The UA was interpolated raw into JS; a quote broke the whole script."""
    from chuscraper.core.stealth import SystemProfile

    nasty = 'Mozilla/5.0 "; window.__pwned = 1; //'
    profile = SystemProfile(user_agent=nasty, _fingerprint={"a": 1})
    config = profile._build_config_script()

    assert "window.__pwned" not in config.replace(json.dumps(nasty), "")
    assert json.dumps(nasty) in config


def test_stealth_scripts_are_injected_separately():
    """One malformed bypass must not be able to disable the others."""
    from chuscraper.core.stealth import SystemProfile

    profile = SystemProfile(user_agent="x", _fingerprint={"a": 1})
    scripts = profile._build_stealth_scripts(145, "145.0.0.0")
    assert len(scripts) > 1


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

def test_socks_proxy_keeps_its_scheme():
    """Stripping the scheme made Chrome treat SOCKS proxies as HTTP."""
    from chuscraper.core.config import Config

    config = Config(proxy="socks5://127.0.0.1:1080", browser_executable_path="/bin/true")
    assert "--proxy-server=socks5://127.0.0.1:1080" in config()


def test_http_proxy_has_no_scheme_prefix():
    from chuscraper.core.config import Config

    config = Config(proxy="http://127.0.0.1:8080", browser_executable_path="/bin/true")
    assert "--proxy-server=127.0.0.1:8080" in config()


def test_unknown_config_kwargs_warn(caplog):
    """`__dict__.update(kwargs)` silently accepted typos like headles=True."""
    from chuscraper.core.config import Config

    with caplog.at_level("WARNING"):
        Config(headles=True, browser_executable_path="/bin/true")
    assert "headles" in caplog.text


# --------------------------------------------------------------------------
# Version
# --------------------------------------------------------------------------

def test_version_has_one_source_of_truth():
    """__init__.py hardcoded 0.19.4 while the package shipped 0.19.9."""
    import chuscraper
    from chuscraper._version import __version__ as canonical

    assert chuscraper.__version__ == canonical
