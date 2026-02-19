from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, TypeVar

from .. import cdp
from .connection import Connection
from pydantic import BaseModel

from .tabs.navigation import NavigationMixin
from .tabs.dom import DomMixin
from .tabs.actions import ActionsMixin
from .tabs.network import NetworkMixin
from .tabs.wait import WaitMixin
from .tabs.storage import StorageMixin
from .tabs.screenshot import ScreenshotMixin
from .tabs.evaluation import EvaluationMixin
from .tabs.window import WindowMixin
from .tabs.extract import ExtractionMixin

if TYPE_CHECKING:
    from .browser import Browser
    from .element import Element

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class Tab(
    Connection, 
    NavigationMixin, 
    DomMixin, 
    ActionsMixin, 
    NetworkMixin, 
    WaitMixin, 
    StorageMixin, 
    ScreenshotMixin, 
    EvaluationMixin,
    WindowMixin,
    ExtractionMixin
):
    """
    :ref:`tab` is the controlling mechanism/connection to a 'target'.

    It aggregates functionality via Mixins:
    - NavigationMixin: navigate, reload, back, forward
    - DomMixin: select, find, query_selector, xpath
    - ActionsMixin: click, type, hover, scroll
    - NetworkMixin: intercept, expect_*, download
    - WaitMixin: wait, sleep, wait_for
    - StorageMixin: cookies, local_storage
    - ScreenshotMixin: screenshot, snapshot, pdf
    - EvaluationMixin: evaluate, evaluate_on_new_document
    - WindowMixin: maximize, minimize, resize
    - ExtractionMixin: markdown, crawl
    """

    browser: Browser | None

    def __init__(
        self,
        websocket_url: str,
        target: cdp.target.TargetInfo,
        browser: Browser | None = None,
        **kwargs: Any,
    ):
        super().__init__(websocket_url, target, browser, **kwargs)
        self.browser = browser
        self._dom = None
        self._window_id = None
        # Track last mouse position for human-like movements (default to top-left safe zone)
        self._last_mouse_x = 0
        self._last_mouse_y = 0
        self._is_stopped = False
        self._timeout = 30.0
        self._download_behavior = None
        self.enabled_domains = []

    @property
    def cdp(self):
        """Shortcut to access cdp domains"""
        return cdp

    @property
    def timeout(self) -> float:
        return self._timeout

    @timeout.setter
    def timeout(self, value: float):
        self._timeout = value

    @property
    def url(self) -> str:
        """Returns the current URL of the tab."""
        if not self.target:
            return ""
        return self.target.url

    @property
    def inspector_url(self) -> str:
        if not self.browser:
            raise ValueError("this tab has no browser attribute")
        return f"http://{self.browser.config.host}:{self.browser.config.port}/devtools/inspector.html?ws={self.websocket_url[5:]}"

    async def close(self):
        """Closes the tab/target."""
        if self.browser:
            await self.send(cdp.target.close_target(self.target_id))

    async def stop(self):
        """Cleanup resources."""
        await self.close()

    async def __call__(
        self,
        text: str | None = None,
        selector: str | None = None,
        timeout: int | float = 10,
    ) -> Element:
        """
        alias to query_selector_all or find_elements_by_text, depending
        on whether text= is set or selector= is set

        :param selector: css selector string
        :return:
        :rtype:
        """
        return await self.wait_for(text, selector, timeout)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Tab):
            return False

        return other.target == self.target

    def __repr__(self) -> str:
        extra = ""
        if self.target is not None and self.target.url:
            extra = f"[url: {self.target.url}]"
        s = f"<{type(self).__name__} [{self.target_id}] [{self.type_}] {extra}>"
        return s
