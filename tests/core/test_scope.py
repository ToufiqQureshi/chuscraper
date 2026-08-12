"""
Guards on chuscraper's scope and dependency surface.

chuscraper is deliberately four pillars: stealth scraping, web automation,
mobile (ADB) scraping/automation, and AI extraction. These tests fail loudly
when something creeps back in - a heavyweight dependency, a re-added side
feature, or a deprecated API that quietly became load-bearing again.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _runtime_deps() -> set[str]:
    """
    Names in [project].dependencies.

    Parsed with a regex rather than tomllib, which is 3.11+ only while this
    package supports 3.10.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text()
    block = re.search(r"^dependencies = \[(.*?)^\]", text, re.S | re.M)
    assert block, "could not find [project].dependencies in pyproject.toml"
    return {
        re.split(r"[><=!~\[]", spec)[0].strip().lower()
        for spec in re.findall(r'"([^"]+)"', block.group(1))
    }


# --------------------------------------------------------------------------
# Dependency surface
# --------------------------------------------------------------------------

@pytest.mark.parametrize("banned", ["playwright", "msgspec", "mss", "curl_cffi", "psutil"])
def test_heavy_dependency_stays_out(banned):
    """
    These were all declared but unused (playwright/msgspec only fed dead route
    handlers, mss only fed tile_windows, curl_cffi was never imported at all,
    psutil is test-only). playwright in particular pulls ~50MB plus browser
    downloads into every install.
    """
    assert banned.replace("_", "-") not in _runtime_deps()
    assert banned not in _runtime_deps()


def test_importing_chuscraper_does_not_need_playwright():
    """`import chuscraper` used to hard-fail without playwright installed."""
    code = (
        "import sys;"
        "sys.modules['playwright'] = None;"
        "import chuscraper;"
        "print(chuscraper.__version__)"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_import_is_warning_free():
    """A plain import must not emit DeprecationWarnings at users."""
    result = subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c", "import chuscraper"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


# --------------------------------------------------------------------------
# The four pillars must keep working
# --------------------------------------------------------------------------

@pytest.mark.parametrize("dotted", [
    "chuscraper.core.stealth:SystemProfile",       # stealth scraping
    "chuscraper.core.tab:Tab",                     # web automation
    "chuscraper.spider.core:Crawler",              # crawling
    "chuscraper.engine.parser:Selector",           # adaptive selectors
    "chuscraper.extractors.markdown:html_to_markdown",
    "chuscraper.mobile:MobileDevice",              # mobile
    "chuscraper.ai.base:BaseExtractor",            # ai
])
def test_pillar_entrypoint_imports(dotted):
    import importlib

    module, _, attr = dotted.partition(":")
    assert getattr(importlib.import_module(module), attr) is not None


# --------------------------------------------------------------------------
# Deprecated surface: still works, still warns
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "Logger", "FailureDumper", "HumanBehavior", "RateLimiter", "SessionManager",
])
def test_deprecated_attr_warns_but_still_works(name, recwarn):
    """Removed in 0.22 - until then they must keep working for existing users."""
    import chuscraper

    obj = getattr(chuscraper, name)
    assert obj is not None
    assert any(issubclass(w.category, DeprecationWarning) for w in recwarn)


def test_unknown_attribute_still_raises_attribute_error():
    """The lazy __getattr__ must not swallow genuine typos."""
    import chuscraper

    with pytest.raises(AttributeError):
        chuscraper.NoSuchThing


def test_removed_helpers_are_gone():
    """tile_windows and the dead engines/ subtree should not come back."""
    from chuscraper.core.browsers.target_manager import TargetManagerMixin

    assert not hasattr(TargetManagerMixin, "tile_windows")
    assert not (REPO_ROOT / "chuscraper" / "engine" / "engines").exists()
