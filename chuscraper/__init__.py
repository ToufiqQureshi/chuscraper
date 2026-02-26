from chuscraper.core.keys import KeyEvents, SpecialKeys, KeyPressEvent, KeyModifiers
from chuscraper.core.observability import Logger, FailureDumper
from chuscraper.core.config import Config
from chuscraper.core.stealth import SystemProfile

BrowserConfig = Config

__version__ = "0.19.4"

__all__ = [
    "__version__",
    "loop",
    "Browser",
    "Tab",
    "cdp",
    "Config",
    "BrowserConfig",
    "start",
    "scrape",
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
from chuscraper.core.util import loop, start, scrape
from chuscraper.core.browser import Browser
from chuscraper.core.tab import Tab
from chuscraper.core.element import Element
from chuscraper.core.connection import Connection
from chuscraper.core._contradict import ContraDict, cdict
from chuscraper.mobile import MobileDevice, MobileElement
from chuscraper import cdp
