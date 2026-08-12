from chuscraper.core.keys import KeyEvents, SpecialKeys, KeyPressEvent, KeyModifiers
from chuscraper.core.config import Config
from chuscraper.core.stealth import SystemProfile

BrowserConfig = Config

# Single source of truth: _version.py is what pyproject/hatch reads, so the
# hardcoded duplicate here had drifted (0.19.4 vs the released 0.19.9).
from chuscraper._version import __version__

__all__ = [
    "__version__",
    "loop",
    "Browser",
    "Tab",
    "cdp",
    "Config",
    "BrowserConfig",
    "start",
    "util",
    "Element",
    "ContraDict",
    "cdict",
    "Connection",
    "KeyEvents",
    "SpecialKeys",
    "KeyPressEvent",
    "KeyModifiers",
    "Logger",
    "FailureDumper",
    "SystemProfile",
    "MobileDevice",
    "MobileElement",
]

# Lazy imports to avoid circular dependencies
from chuscraper.core.util import loop, start
from chuscraper.core.browser import Browser
from chuscraper.core.tab import Tab
from chuscraper.core.element import Element
from chuscraper.core.connection import Connection
from chuscraper.core._contradict import ContraDict, cdict
from chuscraper.mobile import MobileDevice, MobileElement
from chuscraper import cdp


# ── Deprecated, removed in 0.22 ──────────────────────────────────────────────
# Exposed lazily so `import chuscraper` stays warning-free for everyone who
# doesn't actually touch them.
_DEPRECATED_ATTRS = {
    "Logger": ("chuscraper.core.observability", "use the stdlib `logging` module"),
    "FailureDumper": ("chuscraper.core.observability", "handle failure artefacts in your own error path"),
    "HumanBehavior": ("chuscraper.core.behavior", "use the stealth engine and click(mode='human')"),
    "RateLimiter": ("chuscraper.core.limiter", "use asyncio.Semaphore or aiolimiter"),
    "SessionManager": ("chuscraper.core.limiter", "track session duration in your own code"),
}


def __getattr__(name: str):
    if name in _DEPRECATED_ATTRS:
        import importlib
        import warnings

        module_path, advice = _DEPRECATED_ATTRS[name]
        warnings.warn(
            f"chuscraper.{name} is deprecated and will be removed in chuscraper "
            f"0.22 - {advice}.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(importlib.import_module(module_path), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
