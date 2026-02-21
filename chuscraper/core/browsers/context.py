from __future__ import annotations

import asyncio
import logging
import random
import typing
import urllib.parse
import pathlib
import pickle
import re
import http.cookiejar
from .base import BrowserMixin
from ... import cdp

if typing.TYPE_CHECKING:
    from ...core.connection import Connection
    from ...core.config import PathLike
    from ...core.browser import Browser

logger = logging.getLogger(__name__)


class BrowserContextMixin(BrowserMixin):
    @property
    def cookies(self) -> CookieJar:
        if not hasattr(self.browser, "_cookies") or self.browser._cookies is None:
            self.browser._cookies = CookieJar(self.browser)
        return self.browser._cookies

    async def _handle_auth(
        self, event: cdp.fetch.AuthRequired, connection: Connection
    ) -> None:
        """Handles Fetch.authRequired events for proxy authentication."""
        if not self.config.proxy:
            await connection.send(
                cdp.fetch.continue_with_auth(
                    event.request_id, cdp.fetch.AuthChallengeResponse(response="Default")
                )
            )
            return

        parsed = urllib.parse.urlparse(self.config.proxy)
        if "://" not in self.config.proxy:
            parsed = urllib.parse.urlparse("http://" + self.config.proxy)

        username = parsed.username
        password = parsed.password

        if username and password:
            logger.debug(
                f"Handling auth challenge for {event.request.url} on {connection}"
            )
            asyncio.create_task(
                connection.send(
                    cdp.fetch.continue_with_auth(
                        request_id=event.request_id,
                        auth_challenge_response=cdp.fetch.AuthChallengeResponse(
                            response="ProvideCredentials",
                            username=username,
                            password=password,
                        ),
                    )
                )
            )
        else:
            asyncio.create_task(
                connection.send(
                    cdp.fetch.continue_with_auth(
                        event.request_id,
                        cdp.fetch.AuthChallengeResponse(response="Default"),
                    )
                )
            )

    async def _handle_request_paused(
        self, event: cdp.fetch.RequestPaused, connection: Connection
    ) -> None:
        """Handles Fetch.requestPaused. Just continue the request."""

        async def safe_continue() -> None:
            try:
                await connection.send(
                    cdp.fetch.continue_request(request_id=event.request_id)
                )
            except Exception:
                pass

        asyncio.create_task(safe_continue())


    async def grant_all_permissions(self) -> None:
        """grant all browser permissions"""
        if not self.connection:
            raise RuntimeError("Browser connection not initialized")

        permissions = list(cdp.browser.PermissionType)
        permissions.remove(cdp.browser.PermissionType.CAPTURED_SURFACE_CONTROL)
        await self.connection.send(cdp.browser.grant_permissions(permissions))


class CookieJar:
    def __init__(self, browser: Browser):
        self._browser = browser

    async def get_all(
        self, requests_cookie_format: bool = False
    ) -> typing.List[cdp.network.Cookie] | typing.List[http.cookiejar.Cookie]:
        """get all cookies"""
        connection: Connection | None = None
        # Accessing tabs property from Browser (which will use TargetManagerMixin)
        for tab_ in self._browser.tabs:
            if tab_.closed:
                continue
            connection = tab_
            break
        else:
            connection = self._browser.connection

        if not connection:
            raise RuntimeError("Browser not yet started")

        cookies = await connection.send(cdp.storage.get_cookies())
        if requests_cookie_format:
            import requests.cookies

            return [
                requests.cookies.create_cookie(  # type: ignore
                    name=c.name,
                    value=c.value,
                    domain=c.domain,
                    path=c.path,
                    expires=c.expires,
                    secure=c.secure,
                )
                for c in cookies
            ]
        return cookies

    async def set_all(self, cookies: typing.List[cdp.network.CookieParam]) -> None:
        """set cookies"""
        connection: Connection | None = None
        for tab_ in self._browser.tabs:
            if tab_.closed:
                continue
            connection = tab_
            break
        else:
            connection = self._browser.connection

        if not connection:
            raise RuntimeError("Browser not yet started")

        await connection.send(cdp.storage.set_cookies(cookies))

    async def save(self, file: PathLike = ".session.dat", pattern: str = ".*") -> None:
        """save all cookies to a file"""
        compiled_pattern = re.compile(pattern)
        save_path = pathlib.Path(file).resolve()
        cookies = await self.get_all(requests_cookie_format=False)
        included_cookies = []
        for cookie in cookies:
            for match in compiled_pattern.finditer(str(cookie.__dict__)):
                logger.debug(
                    "saved cookie for matching pattern '%s' => (%s: %s)",
                    compiled_pattern.pattern,
                    cookie.name,
                    cookie.value,
                )
                included_cookies.append(cookie)
                break
        pickle.dump(included_cookies, save_path.open("w+b"))

    async def load(self, file: PathLike = ".session.dat", pattern: str = ".*") -> None:
        """load all cookies from a file"""
        save_path = pathlib.Path(file).resolve()
        if not save_path.exists():
            return
        
        compiled_pattern = re.compile(pattern)
        cookies = pickle.load(save_path.open("r+b"))
        included_cookies = []
        for cookie in cookies:
            for match in compiled_pattern.finditer(str(cookie.__dict__)):
                included_cookies.append(cookie)
                logger.debug(
                    "loaded cookie for matching pattern '%s' => (%s: %s)",
                    compiled_pattern.pattern,
                    cookie.name,
                    cookie.value,
                )
                break
        await self.set_all(included_cookies)

    async def clear(self) -> None:
        """clear current cookies"""
        connection: Connection | None = None
        for tab_ in self._browser.tabs:
            if tab_.closed:
                continue
            connection = tab_
            break
        else:
            connection = self._browser.connection

        if not connection:
            raise RuntimeError("Browser not yet started")

        await connection.send(cdp.storage.clear_cookies())
