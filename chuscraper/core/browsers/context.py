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

    async def _apply_stealth_and_timezone(self, tab_obj: typing.Any) -> None:
        """Applies stealth scripts, timezone, and locale overrides to a tab."""
        # 0. Enable core domains
        try:
            await tab_obj.send(cdp.dom.enable())
            await tab_obj.send(cdp.runtime.enable())
            await tab_obj.send(cdp.page.enable())
        except Exception as e:
            logger.debug(f"Failed to enable domains for {tab_obj}: {e}")

        # 1. Setup Timezone
        if self.config.timezone:
            try:
                await tab_obj.send(
                    cdp.emulation.set_timezone_override(self.config.timezone)
                )
            except Exception as e:
                logger.debug(f"Failed to set timezone for {tab_obj}: {e}")

        # 2. Setup Locale
        lang = self.config.lang or "en-US"
        try:
            await tab_obj.send(cdp.emulation.set_locale_override(locale=lang))
        except Exception as e:
            logger.debug(f"Failed to set locale for {tab_obj}: {e}")

        # 3. Setup Stealth Scripts
        if self.config.stealth:
            if not hasattr(self.config, "_stealth_seed"):
                self.config._stealth_seed = random.randint(1, 1000000)

            from .. import stealth

            # Pass detected browser version for coherence
            browser_version = getattr(self, "version", None)
            scripts, profile = stealth.get_stealth_scripts(self.config, browser_version)

            # Apply CDP overrides for robust stealth (Network + JS consistency)
            if self.config.user_agent:
                try:
                    await tab_obj.send(cdp.emulation.set_user_agent_override(
                        user_agent=self.config.user_agent,
                        accept_language=self.config.lang or "en-US",
                        platform=profile.platform
                    ))
                except Exception as e:
                    logger.debug(f"Failed to override UA: {e}")

            # Override device metrics (Screen size)
            try:
                await tab_obj.send(cdp.emulation.set_device_metrics_override(
                    width=profile.screen_width,
                    height=profile.screen_height,
                    device_scale_factor=1,
                    mobile=False
                ))
            except Exception as e:
                logger.debug(f"Failed to override metrics: {e}")

            for script in scripts:
                try:
                    await tab_obj.send(
                        cdp.page.add_script_to_evaluate_on_new_document(
                            source=script,
                            run_immediately=True # Ensure immediate execution if supported by protocol version
                        )
                    )
                except Exception as e:
                    # Fallback for older protocol versions
                    try:
                        await tab_obj.send(
                            cdp.page.add_script_to_evaluate_on_new_document(source=script)
                        )
                    except Exception:
                        logger.debug(f"Failed to add stealth script to {tab_obj}: {e}")

        # 4. Set realistic request headers for first-party consistency
        try:
            await tab_obj.send(cdp.network.enable())
            await tab_obj.send(cdp.network.set_extra_http_headers(headers={
                "Accept-Language": lang,
                "Upgrade-Insecure-Requests": "1",
                "DNT": "1",
            }))
        except Exception as e:
            logger.debug(f"Failed to set extra headers for {tab_obj}: {e}")

        # 5. Optional startup humanization
        if self.config.humanize:
            await self._humanize_startup(tab_obj)


    async def _humanize_startup(self, tab_obj: typing.Any) -> None:
        """Adds subtle human-like warmup events to reduce deterministic startup patterns."""
        min_delay = max(0.01, float(getattr(self.config, "humanize_min_delay", 0.08)))
        max_delay = max(min_delay, float(getattr(self.config, "humanize_max_delay", 0.35)))

        try:
            await asyncio.sleep(random.uniform(min_delay, max_delay))

            viewport = await tab_obj.send(cdp.page.get_layout_metrics())
            width = max(300, int(viewport.css_layout_viewport.client_width))
            height = max(300, int(viewport.css_layout_viewport.client_height))

            points = [
                (random.randint(20, width // 2), random.randint(20, height // 2)),
                (random.randint(width // 3, width - 20), random.randint(height // 4, height - 20)),
            ]
            for x, y in points:
                await tab_obj.send(cdp.input_.dispatch_mouse_event(type_="mouseMoved", x=float(x), y=float(y)))
                await asyncio.sleep(random.uniform(min_delay / 2, max_delay / 2))

            wheel_delta = random.choice([80.0, 120.0, 160.0])
            await tab_obj.send(cdp.input_.dispatch_mouse_event(
                type_="mouseWheel",
                x=float(points[-1][0]),
                y=float(points[-1][1]),
                delta_y=wheel_delta,
            ))
            await asyncio.sleep(random.uniform(min_delay, max_delay))
        except Exception as e:
            logger.debug(f"Failed startup humanization for {tab_obj}: {e}")

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
