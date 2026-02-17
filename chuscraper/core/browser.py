from __future__ import annotations

import asyncio
import copy
import http
import http.cookiejar
import json
import logging
import pathlib
import pickle
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
import warnings
from collections import defaultdict
from typing import List, Tuple, Union, Any

import asyncio_atexit

from .. import cdp
from . import tab, util, stealth
from ._contradict import ContraDict
from .config import BrowserType, Config, PathLike, is_posix
from .connection import Connection

logger = logging.getLogger(__name__)


class Browser:
    """
    The Browser object is the "root" of the hierarchy and contains a reference
    to the browser parent process.
    there should usually be only 1 instance of this.

    All opened tabs, extra browser screens and resources will not cause a new Browser process,
    but rather create additional :class:`chuscraper.Tab` objects.

    So, besides starting your instance and first/additional tabs, you don't actively use it a lot under normal conditions.

    Tab objects will represent and control
     - tabs (as you know them)
     - browser windows (new window)
     - iframe
     - background processes

    note:
    the Browser object is not instantiated by __init__ but using the asynchronous :meth:`chuscraper.Browser.create` method.

    note:
    in Chromium based browsers, there is a parent process which keeps running all the time, even if
    there are no visible browser windows. sometimes it's stubborn to close it, so make sure after using
    this library, the browser is correctly and fully closed/exited/killed.

    """

    _process: subprocess.Popen[bytes] | None
    _process_pid: int | None
    _http: HTTPApi | None = None
    _cookies: CookieJar | None = None
    _update_target_info_mutex: asyncio.Lock = asyncio.Lock()
    _local_proxy: Any | None = None

    config: Config
    connection: Connection | None

    @classmethod
    async def create(
        cls,
        config: Config | None = None,
        *,
        user_data_dir: PathLike | None = None,
        headless: bool = False,
        user_agent: str | None = None,
        browser_executable_path: PathLike | None = None,
        browser: BrowserType = "auto",
        browser_args: List[str] | None = None,
        sandbox: bool = True,
        lang: str | None = None,
        host: str | None = None,
        port: int | None = None,
        **kwargs: Any,
    ) -> Browser:
        """
        entry point for creating an instance
        """
        if not config:
            config = Config(
                user_data_dir=user_data_dir,
                headless=headless,
                user_agent=user_agent,
                browser_executable_path=browser_executable_path,
                browser=browser,
                browser_args=browser_args or [],
                sandbox=sandbox,
                lang=lang,
                host=host,
                port=port,
                **kwargs,
            )
        instance = cls(config)
        await instance.start()

        async def browser_atexit() -> None:
            if not instance.stopped:
                await instance.stop()
            await instance._cleanup_temporary_profile()

        asyncio_atexit.register(browser_atexit)

        return instance

    def __init__(self, config: Config):
        """
        constructor. to create a instance, use :py:meth:`Browser.create(...)`

        :param config:
        """

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError(
                "{0} objects of this class are created using await {0}.create()".format(
                    self.__class__.__name__
                )
            )
        # weakref.finalize(self, self._quit, self)

        # each instance gets it's own copy so this class gets a copy that it can
        # use to help manage the browser instance data (needed for multiple browsers)
        self.config = copy.deepcopy(config)

        self.targets: List[Connection] = []
        """current targets (all types)"""
        self.info: ContraDict | None = None
        self._target = None
        self._process = None
        self._process_pid = None
        self._is_updating = asyncio.Event()
        self.connection = None
        self._local_proxy = None
        logger.debug("Session object initialized: %s" % vars(self))

    @property
    def websocket_url(self) -> str:
        if not self.info:
            raise RuntimeError("Browser not yet started. use await browser.start()")

        return self.info.webSocketDebuggerUrl  # type: ignore

    @property
    def main_tab(self) -> tab.Tab | None:
        """returns the target which was launched with the browser"""
        results = sorted(self.targets, key=lambda x: x.type_ == "page", reverse=True)
        if len(results) > 0:
            result = results[0]
            if isinstance(result, tab.Tab):
                return result
        return None

    @property
    def tabs(self) -> List[tab.Tab]:
        """returns the current targets which are of type "page"
        :return:
        """
        tabs = filter(lambda item: item.type_ == "page", self.targets)
        return list(tabs)  # type: ignore

    @property
    def cookies(self) -> CookieJar:
        if not self._cookies:
            self._cookies = CookieJar(self)
        return self._cookies

    @property
    def stopped(self) -> bool:
        return not (self._process and self._process.poll() is None)

    async def wait(self, time: Union[float, int] = 1) -> Browser:
        """wait for <time> seconds. important to use, especially in between page navigation

        :param time:
        :return:
        """
        return await asyncio.sleep(time, result=self)

    sleep = wait
    """alias for wait"""

    async def _handle_target_update(
        self,
        event: Union[
            cdp.target.TargetInfoChanged,
            cdp.target.TargetDestroyed,
            cdp.target.TargetCreated,
            cdp.target.TargetCrashed,
        ],
    ) -> None:
        """this is an internal handler which updates the targets when chrome emits the corresponding event"""

        async with self._update_target_info_mutex:
            if isinstance(event, cdp.target.TargetInfoChanged):
                target_info = event.target_info

                current_tab = next(
                    filter(
                        lambda item: item.target_id == target_info.target_id,
                        self.targets,
                    ),
                    None
                )
                if not current_tab:
                    logger.debug(f"TargetInfoChanged for unknown target {target_info.target_id}")
                    return

                current_target = current_tab.target

                if logger.getEffectiveLevel() <= 10:
                    changes = util.compare_target_info(current_target, target_info)
                    changes_string = ""
                    for change in changes:
                        key, old, new = change
                        changes_string += f"\n{key}: {old} => {new}\n"
                    logger.debug(
                        "target #%d has changed: %s"
                        % (self.targets.index(current_tab), changes_string)
                    )

                current_tab.target = target_info

            elif isinstance(event, cdp.target.TargetCreated):
                target_info = event.target_info
                from .tab import Tab

                new_target = Tab(
                    (
                        f"ws://{self.config.host}:{self.config.port}"
                        f"/devtools/{target_info.type_ or 'page'}"  # all types are 'page' internally in chrome apparently
                        f"/{target_info.target_id}"
                    ),
                    target=target_info,
                    browser=self,
                )

                self.targets.append(new_target)
                
                # Apply stealth/timezone to new target
                # We do this asynchronously to avoid blocking the main event handler
                asyncio.create_task(self._apply_stealth_and_timezone(new_target))

                logger.debug("target #%d created => %s", len(self.targets), new_target)

            elif isinstance(event, cdp.target.TargetDestroyed):
                current_tab = next(
                    filter(lambda item: item.target_id == event.target_id, self.targets),
                    None
                )
                if current_tab:
                    logger.debug(
                        "target removed. id # %d => %s"
                        % (self.targets.index(current_tab), current_tab)
                    )
                    self.targets.remove(current_tab)

            elif isinstance(event, cdp.target.TargetCrashed):
                logger.error(f"CRITICAL: Target Crashed! ID: {event.target_id} Status: {event.status} Error: {event.error_code}")
                current_tab = next(
                    filter(lambda item: item.target_id == event.target_id, self.targets),
                    None
                )
                if current_tab:
                    logger.warning(f"Removing crashed target from list: {current_tab}")
                    self.targets.remove(current_tab)

    async def _handle_auth(self, event: cdp.fetch.AuthRequired, connection: Connection) -> None:
        """
        Handles Fetch.authRequired events for proxy authentication.
        """
        if not self.config.proxy:
             await connection.send(cdp.fetch.continue_with_auth(event.request_id, cdp.fetch.AuthChallengeResponse(response="Default")))
             return

        import urllib.parse
        parsed = urllib.parse.urlparse(self.config.proxy)
        if "://" not in self.config.proxy:
             parsed = urllib.parse.urlparse("http://" + self.config.proxy)

        username = parsed.username
        password = parsed.password
        
        if username and password:
            logger.debug(f"Handling auth challenge for {event.request.url} on {connection}")
            # Run in background to avoid blocking the read loop with a send-await-read cycle
            asyncio.create_task(connection.send(
                cdp.fetch.continue_with_auth(
                    request_id=event.request_id,
                    auth_challenge_response=cdp.fetch.AuthChallengeResponse(
                        response="ProvideCredentials",
                        username=username,
                        password=password
                    )
                )
            ))
        else:
            asyncio.create_task(connection.send(cdp.fetch.continue_with_auth(event.request_id, cdp.fetch.AuthChallengeResponse(response="Default"))))


    async def _handle_request_paused(self, event: cdp.fetch.RequestPaused, connection: Connection) -> None:
        """
        Handles Fetch.requestPaused. We just continue the request.
        """
        async def safe_continue() -> None:
            try:
                # continue_request is a command, it waits for a response (ack).
                # So we should run it in background to free up the read loop.
                await connection.send(cdp.fetch.continue_request(request_id=event.request_id))
            except Exception:
                # Ignore errors if request is already closed or invalid interception ID
                pass

        asyncio.create_task(safe_continue())

    async def _handle_attached_to_target(self, event: cdp.target.AttachedToTarget) -> None:
        """
        Handles Target.attachedToTarget.
        Injects stealth scripts into workers/frames if waiting for debugger.
        """
        session_id = event.session_id
        target_info = event.target_info
        
        if event.waiting_for_debugger:
            try:
                # Only apply if stealth is enabled
                if self.config.stealth:
                    scripts = stealth.get_stealth_scripts()
                    
                    # For Workers/ServiceWorkers: Use Runtime.evaluate
                    if target_info.type_ in ["worker", "service_worker", "shared_worker"]:
                        for script in scripts:
                            await self.connection.send(
                                cdp.runtime.evaluate(expression=script),
                                session_id=session_id
                            )
                            
                    # For Pages/Iframes: Use Page.addScriptToEvaluateOnNewDocument
                    elif target_info.type_ in ["page", "iframe"]:
                        for script in scripts:
                            await self.connection.send(
                                cdp.page.add_script_to_evaluate_on_new_document(source=script),
                                session_id=session_id
                            )
                            
                # Resume execution
                await self.connection.send(
                    cdp.runtime.run_if_waiting_for_debugger(),
                    session_id=session_id
                )
            except Exception as e:
                logger.error(f"Failed to handle attached target {target_info.target_id}: {e}")

    async def _apply_stealth_and_timezone(self, tab_obj: tab.Tab) -> None:
        """
        Applies stealth scripts, timezone override to a tab.
        PATCHRIGHT-LEVEL: Proxy auth handled by Extension (not CDP Fetch).
        CDP Fetch.enable causes ALL requests to pause, leading to hangs.
        """
        # 1. Proxy Auth: Handled by Chrome Extension (loaded in start())
        # Extension uses chrome.proxy.settings + onAuthRequired
        # This is the ONLY reliable method that doesn't hang.

        # 2. Setup Timezone
        if self.config.timezone:
            try:
                await tab_obj.send(cdp.emulation.set_timezone_override(self.config.timezone))
            except Exception as e:
                logger.debug(f"Failed to set timezone for {tab_obj}: {e}")

        # 3. Setup Stealth Scripts
        if self.config.stealth:
            scripts = stealth.get_stealth_scripts()
            for script in scripts:
                try:
                    await tab_obj.send(cdp.page.add_script_to_evaluate_on_new_document(source=script))
                except Exception as e:
                    logger.debug(f"Failed to add stealth script to {tab_obj}: {e}")

    async def get(
        self, url: str = "about:blank", new_tab: bool = False, new_window: bool = False
    ) -> tab.Tab:
        """top level get. utilizes the first tab to retrieve given url.

        convenience function known from selenium.
        this function handles waits/sleeps and detects when DOM events fired, so it's the safest
        way of navigating.

        :param url: the url to navigate to
        :param new_tab: open new tab
        :param new_window:  open new window
        :return: Page
        :raises asyncio.TimeoutError:
        """
        if new_window and not new_tab:
            new_tab = True

        if not self.tabs or new_tab:
            target = await self.send(
                cdp.target.create_target(
                    "about:blank", new_window=new_window, background=False
                )
            )

            # we wait for the TargetCreated event to be processed
            # and our Tab object to be instantiated
            loop = asyncio.get_running_loop()
            start_time = loop.time()
            while True:
                tab_obj = next(
                    (t for t in self.tabs if t.target_id == target),
                    None,
                )
                if tab_obj:
                    break
                await asyncio.sleep(0.01)
                if loop.time() - start_time > self.config.browser_connection_timeout:
                    raise asyncio.TimeoutError("Timeout waiting for new tab")

            # apply stealth and timezone
            await self._apply_stealth_and_timezone(tab_obj)

            if url != "about:blank":
                await tab_obj.get(url)
            return tab_obj

        else:
            p = self.main_tab
            if not p:
                return await self.get(url, new_tab=True)
            await p.get(url)
            return p

    async def goto(self, url: str) -> tab.Tab:
        """Shortcut for browser.main_tab.get(url)."""
        return await self.main_tab.get(url)

    async def scrape(self, selector: str, timeout: Union[int, float] = 10):
        """Shortcut for browser.main_tab.select(selector)."""
        return await self.main_tab.select(selector, timeout=timeout)

    async def start(self) -> Browser:
        """launches the actual browser"""
        if not self:
            raise ValueError(
                "Cannot be called as a class method. Use `await Browser.create()` to create a new instance"
            )

        if self._process or self._process_pid:
            if self._process and self._process.returncode is not None:
                return await self.create(config=self.config)
            warnings.warn("ignored! this call has no effect when already running.")
            return self

        connect_existing = False
        if self.config.host is not None and self.config.port is not None:
            connect_existing = True
        else:
            self.config.host = "127.0.0.1"
            self.config.port = util.free_port()

        if not connect_existing:
            logger.debug(
                "BROWSER EXECUTABLE PATH: %s", self.config.browser_executable_path
            )
            if not pathlib.Path(self.config.browser_executable_path).exists():
                raise FileNotFoundError(
                    (
                        """
                    ---------------------
                    Could not determine browser executable.
                    ---------------------
                    Make sure your browser is installed in the default location (path).
                    If you are sure about the browser executable, you can specify it using
                    the `browser_executable_path='{}` parameter."""
                    ).format(
                        "/path/to/browser/executable"
                        if is_posix
                        else "c:/path/to/your/browser.exe"
                    )
                )

        if getattr(self.config, "_extensions", None):  # noqa
            self.config.add_argument(
                "--load-extension=%s"
                % ",".join(str(_) for _ in self.config._extensions)
            )  # noqa

        # PATCHRIGHT-LEVEL: Local Proxy Forwarding (The "Golden Standard")
        # Instead of Extensions or CDP (which fail/hang), we start a local TCP proxy
        # that handles upstream authentication transparently.
        # Chrome just sees an open proxy on localhost.
        if self.config.proxy:
             from . import local_proxy
             
             # Start local proxy
             self._local_proxy = local_proxy.LocalAuthProxy(self.config.proxy)
             local_port = await self._local_proxy.start()
             
             # Point Chrome to local proxy
             # This overrides the original proxy string in config
             # ensuring config() generates the correct --proxy-server flag
             original_proxy = self.config.proxy
             self.config.proxy = f"http://127.0.0.1:{local_port}"
             logger.info(f"Started Local Auth Proxy: 127.0.0.1:{local_port} -> {original_proxy}")

        exe = self.config.browser_executable_path
        params = self.config()
        
        # Note: --disable-blink-features=AutomationControlled is now in
        # config._default_browser_args. No need to add it here.
        
        params.append("about:blank")

        logger.info(
            "starting\n\texecutable :%s\n\narguments:\n%s", exe, "\n\t".join(params)
        )
        if not connect_existing:
            self._process = util._start_process(exe, params, is_posix)
            self._process_pid = self._process.pid

        self._http = HTTPApi((self.config.host, self.config.port))
        util.get_registered_instances().add(self)
        await asyncio.sleep(self.config.browser_connection_timeout)
        for _ in range(self.config.browser_connection_max_tries):
            if await self.test_connection():
                break

            await asyncio.sleep(self.config.browser_connection_timeout)

        if not self.info:
            if self._process is not None:
                stderr = await util._read_process_stderr(self._process)
                logger.info(
                    "Browser stderr: %s", stderr if stderr else "No output from browser"
                )

            await self.stop()
            raise Exception(
                (
                    """
                ---------------------
                Failed to connect to browser
                ---------------------
                One of the causes could be when you are running as root.
                In that case you need to pass no_sandbox=True
                """
                )
            )

        self.connection = Connection(self.info.webSocketDebuggerUrl, _owner=self)

        if self.config.autodiscover_targets:
            logger.info("enabling autodiscover targets")

            # self.connection.add_handler(
            #     cdp.target.TargetInfoChanged, self._handle_target_update
            # )
            # self.connection.add_handler(
            #     cdp.target.TargetCreated, self._handle_target_update
            # )
            # self.connection.add_handler(
            #     cdp.target.TargetDestroyed, self._handle_target_update
            # )
            # self.connection.add_handler(
            #     cdp.target.TargetCreated, self._handle_target_update
            # )
            #
            self.connection.handlers[cdp.target.TargetInfoChanged] = [
                self._handle_target_update
            ]
            self.connection.handlers[cdp.target.TargetCreated] = [
                self._handle_target_update
            ]
            self.connection.handlers[cdp.target.TargetDestroyed] = [
                self._handle_target_update
            ]
            self.connection.handlers[cdp.target.TargetCrashed] = [
                self._handle_target_update
            ]
            # Handle auto-attached targets (Workers, Iframes) for stealth injection
            self.connection.handlers[cdp.target.AttachedToTarget] = [
                self._handle_attached_to_target
            ]
            
            await self.connection.send(cdp.target.set_discover_targets(discover=True))
            await self.connection.send(
                cdp.target.set_auto_attach(
                    auto_attach=True, wait_for_debugger_on_start=True, flatten=True
                )
            )
        await self.update_targets()
        
        # Apply stealth/timezone to initial targets
        for t in self.tabs:
            await self._apply_stealth_and_timezone(t)
            
        return self

    async def test_connection(self) -> bool:
        if not self._http:
            raise ValueError("HTTPApi not yet initialized")

        try:
            self.info = ContraDict(await self._http.get("version"), silent=True)
            return True
        except Exception:
            logger.debug("Could not start", exc_info=True)
            return False

    async def grant_all_permissions(self) -> None:
        """
        grant permissions for:
            accessibilityEvents
            audioCapture
            backgroundSync
            backgroundFetch
            clipboardReadWrite
            clipboardSanitizedWrite
            displayCapture
            durableStorage
            geolocation
            idleDetection
            localFonts
            midi
            midiSysex
            nfc
            notifications
            paymentHandler
            periodicBackgroundSync
            protectedMediaIdentifier
            sensors
            storageAccess
            topLevelStorageAccess
            videoCapture
            videoCapturePanTiltZoom
            wakeLockScreen
            wakeLockSystem
            windowManagement
        """
        if not self.connection:
            raise RuntimeError("Browser not yet started. use await browser.start()")

        permissions = list(cdp.browser.PermissionType)
        permissions.remove(cdp.browser.PermissionType.CAPTURED_SURFACE_CONTROL)
        await self.connection.send(cdp.browser.grant_permissions(permissions))

    async def tile_windows(
        self, windows: List[tab.Tab] | None = None, max_columns: int = 0
    ) -> List[List[int]]:
        import math

        import mss

        m = mss.mss()
        screen, screen_width, screen_height = 3 * (None,)
        if m.monitors and len(m.monitors) >= 1:
            screen = m.monitors[0]
            screen_width = screen["width"]
            screen_height = screen["height"]
        if not screen or not screen_width or not screen_height:
            warnings.warn("no monitors detected")
            return []
        await self.update_targets()
        distinct_windows = defaultdict(list)

        if windows:
            tabs = windows
        else:
            tabs = self.tabs
        for tab_ in tabs:
            window_id, bounds = await tab_.get_window()
            distinct_windows[window_id].append(tab_)

        num_windows = len(distinct_windows)
        req_cols = max_columns or int(num_windows * (19 / 6))
        req_rows = int(num_windows / req_cols)

        while req_cols * req_rows < num_windows:
            req_rows += 1

        box_w = math.floor((screen_width / req_cols) - 1)
        box_h = math.floor(screen_height / req_rows)

        distinct_windows_iter = iter(distinct_windows.values())
        grid = []
        for x in range(req_cols):
            for y in range(req_rows):
                try:
                    tabs = next(distinct_windows_iter)
                except StopIteration:
                    continue
                if not tabs:
                    continue
                tab_ = tabs[0]

                try:
                    pos = [x * box_w, y * box_h, box_w, box_h]
                    grid.append(pos)
                    await tab_.set_window_size(*pos)
                except Exception:
                    logger.info(
                        "could not set window size. exception => ", exc_info=True
                    )
                    continue
        return grid

    async def _get_targets(self) -> List[cdp.target.TargetInfo]:
        if not self.connection:
            raise RuntimeError("Browser not yet started. use await browser.start()")
        info = await self.connection.send(cdp.target.get_targets(), _is_update=True)
        return info

    async def update_targets(self) -> None:
        targets: List[cdp.target.TargetInfo]
        targets = await self._get_targets()
        for t in targets:
            for existing_tab in self.targets:
                if existing_tab.target_id == t.target_id:
                    existing_tab.target.__dict__.update(t.__dict__)
                    break
            else:
                self.targets.append(
                    tab.Tab(
                        (
                            f"ws://{self.config.host}:{self.config.port}"
                            f"/devtools/page"  # all types are 'page' somehow
                            f"/{t.target_id}"
                        ),
                        target=t,
                        browser=self,
                    )
                )

        await asyncio.sleep(0)

    async def __aenter__(self) -> Browser:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: Any, exc_tb: Any
    ) -> None:
        await self.stop()
        if exc_type:
            # Let Python propagate the exception
            return False

    def __iter__(self) -> Browser:
        main_tab = self.main_tab
        if not main_tab:
            return self
        self._i = self.tabs.index(main_tab)
        return self

    def __reversed__(self) -> List[tab.Tab]:
        return list(reversed(list(self.tabs)))

    def __next__(self) -> tab.Tab:
        try:
            return self.tabs[self._i]
        except IndexError:
            del self._i
            raise StopIteration
        except AttributeError:
            del self._i
            raise StopIteration
        finally:
            if hasattr(self, "_i"):
                if self._i != len(self.tabs):
                    self._i += 1
                else:
                    del self._i

    async def stop(self) -> None:
        """
        Stop the browser instance, including local proxies and temporary files.
        Ensures proper cleanup of zombie processes.
        """
        if self.connection and not self.connection.closed:
            try:
                await self.connection.send(cdp.browser.close())
            except Exception:
                logger.warning(
                    "Could not send the close command when stopping the browser. Likely the browser is already gone. Closing the connection."
                )
            await self.connection.aclose()
            logger.debug("closed the connection")

        if self._process:
            try:
                self._process.terminate()
                try:
                    import subprocess
                    await asyncio.to_thread(self._process.wait, timeout=3.0)
                except (asyncio.TimeoutError, subprocess.TimeoutExpired):
                    logger.warning("Browser process did not terminate gracefully, sending KILL signal.")
                    self._process.kill()
                    await asyncio.to_thread(self._process.wait)
            except ProcessLookupError:
                pass
            except Exception as e:
                logger.error(f"Error while stopping browser process: {e}")
                
        self._process = None
        self._process_pid = None

        # Stop local proxy if it exists
        if self._local_proxy:
            try:
                await self._local_proxy.stop()
                logger.debug("Stopped local proxy")
            except Exception as e:
                logger.debug(f"Error stopping local proxy: {e}")
            self._local_proxy = None

        await self._cleanup_temporary_profile()

    async def _cleanup_temporary_profile(self) -> None:
        if not self.config or self.config.uses_custom_data_dir:
            return

        user_data_path = pathlib.Path(self.config.user_data_dir)

        # Exponential backoff retry logic for deletion
        # This is crucial for Windows where files might be briefly locked
        for attempt in range(10):
            try:
                if user_data_path.exists():
                    shutil.rmtree(self.config.user_data_dir, ignore_errors=False)
                logger.debug(
                    "successfully removed temp profile %s" % self.config.user_data_dir
                )
                return
            except FileNotFoundError:
                return
            except (PermissionError, OSError) as e:
                wait_time = 0.1 * (1.5 ** attempt) # 0.1, 0.15, 0.225...
                if attempt > 5:
                    logger.debug(
                        f"Retry {attempt+1}/10: Could not remove data dir {self.config.user_data_dir} ({e}). Waiting {wait_time:.2f}s"
                    )

                if attempt == 9:
                    logger.warning(
                        "FINAL FAILURE: Could not remove temporary profile %s. You may need to delete it manually.\nError: %s",
                        self.config.user_data_dir,
                        e,
                    )
                await asyncio.sleep(wait_time)
                continue

    def __del__(self) -> None:
        pass


class CookieJar:
    def __init__(self, browser: Browser):
        self._browser = browser
        # self._connection = connection

    async def get_all(
        self, requests_cookie_format: bool = False
    ) -> list[cdp.network.Cookie] | list[http.cookiejar.Cookie]:
        """
        get all cookies

        :param requests_cookie_format: when True, returns python http.cookiejar.Cookie objects, compatible  with requests library and many others.
        :return:
        :rtype:

        """
        connection: Connection | None = None
        for tab_ in self._browser.tabs:
            if tab_.closed:
                continue
            connection = tab_
            break
        else:
            connection = self._browser.connection
        if not connection:
            raise RuntimeError("Browser not yet started. use await browser.start()")

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

    async def set_all(self, cookies: List[cdp.network.CookieParam]) -> None:
        """
        set cookies

        :param cookies: list of cookies
        :return:
        :rtype:
        """
        connection: Connection | None = None
        for tab_ in self._browser.tabs:
            if tab_.closed:
                continue
            connection = tab_
            break
        else:
            connection = self._browser.connection
        if not connection:
            raise RuntimeError("Browser not yet started. use await browser.start()")

        await connection.send(cdp.storage.set_cookies(cookies))

    async def save(self, file: PathLike = ".session.dat", pattern: str = ".*") -> None:
        """
        save all cookies (or a subset, controlled by `pattern`) to a file to be restored later

        :param file:
        :param pattern: regex style pattern string.
               any cookie that has a  domain, key or value field which matches the pattern will be included.
               default = ".*"  (all)

               eg: the pattern "(cf|.com|nowsecure)" will include those cookies which:
                    - have a string "cf" (cloudflare)
                    - have ".com" in them, in either domain, key or value field.
                    - contain "nowsecure"
        :return:
        :rtype:
        """
        compiled_pattern = re.compile(pattern)
        save_path = pathlib.Path(file).resolve()
        connection: Connection | None = None
        for tab_ in self._browser.tabs:
            if tab_.closed:
                continue
            connection = tab_
            break
        else:
            connection = self._browser.connection
        if not connection:
            raise RuntimeError("Browser not yet started. use await browser.start()")

        cookies: (
            list[cdp.network.Cookie] | list[http.cookiejar.Cookie]
        ) = await connection.send(cdp.storage.get_cookies())
        # if not connection:
        #     return
        # if not connection.websocket:
        #     return
        # if connection.websocket.closed:
        #     return
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
        pickle.dump(cookies, save_path.open("w+b"))

    async def load(self, file: PathLike = ".session.dat", pattern: str = ".*") -> None:
        """
        load all cookies (or a subset, controlled by `pattern`) from a file created by :py:meth:`~save_cookies`.

        :param file:
        :param pattern: regex style pattern string.
               any cookie that has a  domain, key or value field which matches the pattern will be included.
               default = ".*"  (all)

               eg: the pattern "(cf|.com|nowsecure)" will include those cookies which:
                    - have a string "cf" (cloudflare)
                    - have ".com" in them, in either domain, key or value field.
                    - contain "nowsecure"
        :return:
        :rtype:
        """
        import re

        compiled_pattern = re.compile(pattern)
        save_path = pathlib.Path(file).resolve()
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
        """
        clear current cookies

        note: this includes all open tabs/windows for this browser

        :return:
        :rtype:
        """
        connection: Connection | None = None
        for tab_ in self._browser.tabs:
            if tab_.closed:
                continue
            connection = tab_
            break
        else:
            connection = self._browser.connection
        if not connection:
            raise RuntimeError("Browser not yet started. use await browser.start()")

        await connection.send(cdp.storage.clear_cookies())


class HTTPApi:
    def __init__(self, addr: Tuple[str, int]):
        self.host, self.port = addr
        self.api = "http://%s:%d" % (self.host, self.port)

    async def get(self, endpoint: str) -> Any:
        return await self._request(endpoint)

    async def post(self, endpoint: str, data: dict[str, str]) -> Any:
        return await self._request(endpoint, method="post", data=data)

    async def _request(
        self, endpoint: str, method: str = "get", data: dict[str, str] | None = None
    ) -> Any:
        url = urllib.parse.urljoin(
            self.api, f"json/{endpoint}" if endpoint else "/json"
        )
        if data and method.lower() == "get":
            raise ValueError("get requests cannot contain data")
        if not url:
            url = self.api + endpoint
        request = urllib.request.Request(url)
        request.method = method
        request.data = None
        if data:
            request.data = json.dumps(data).encode("utf-8")

        response = await asyncio.get_running_loop().run_in_executor(
            None, lambda: urllib.request.urlopen(request, timeout=10)
        )
        return json.loads(response.read())
