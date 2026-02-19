from __future__ import annotations

import asyncio
import copy
import json
import logging
import pathlib
import random
import shutil
import subprocess
import urllib.parse
import urllib.request
import warnings
import re
from typing import List, Tuple, Union, Any

import asyncio_atexit

from .. import cdp
from . import util
from ._contradict import ContraDict
from .config import BrowserType, Config, PathLike, is_posix
import pathlib
from .connection import Connection
from .banner import print_banner

# Import Mixins
from .browsers.target_manager import TargetManagerMixin
from .browsers.context import BrowserContextMixin, CookieJar

logger = logging.getLogger(__name__)


class Browser(TargetManagerMixin, BrowserContextMixin):
    """
    The Browser object is the "root" of the hierarchy and contains a reference
    to the browser parent process.
    """

    _process: subprocess.Popen[bytes] | None
    _process_pid: int | None
    _http: HTTPApi | None = None
    _cookies: CookieJar | None = None
    _update_target_info_mutex: asyncio.Lock = asyncio.Lock()
    _local_proxy: Any | None = None

    _config: Config
    _connection: Connection | None

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
        """entry point for creating an instance"""
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

        # Display banner on first creation
        print_banner()

        await instance.start()

        async def browser_atexit() -> None:
            if not instance.stopped:
                await instance.stop()
            await instance._cleanup_temporary_profile()

        asyncio_atexit.register(browser_atexit)

        return instance

    def __init__(self, config: Config):
        """constructor. to create a instance, use :py:meth:`Browser.create(...)`"""

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError(
                "{0} objects of this class are created using await {0}.create()".format(
                    self.__class__.__name__
                )
            )

        self._config = copy.deepcopy(config)
        self._targets: List[Connection] = []
        self.info: ContraDict | None = None
        self._target = None
        self._process = None
        self._process_pid = None
        self._is_updating = asyncio.Event()
        self._connection = None
        self._local_proxy = None
        self._browser = self  # For BrowserMixin access
        logger.debug("Session object initialized: %s" % vars(self))

        # Setup logging if enabled
        if getattr(self._config, "logging", False):
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            logger.setLevel(logging.INFO)

    @property
    def websocket_url(self) -> str:
        if not self.info:
            raise RuntimeError("Browser not yet started. use await browser.start()")

        return self.info.webSocketDebuggerUrl  # type: ignore

    @property
    def stopped(self) -> bool:
        return not (self._process and self._process.poll() is None)

    async def wait(self, time: Union[float, int] = 1) -> Browser:
        """wait for <time> seconds."""
        return await asyncio.sleep(time, result=self)

    sleep = wait

    async def start(self) -> Browser:
        """launches the actual browser"""
        if self._process or self._process_pid:
            if self._process and self._process.returncode is not None:
                return await self.create(config=self._config)
            warnings.warn("ignored! this call has no effect when already running.")
            return self

        connect_existing = False
        if self._config.host is not None and self._config.port is not None:
            connect_existing = True
        else:
            self._config.host = "127.0.0.1"
            # Use 0 to let Chrome pick a port, preventing race conditions
            self._config.port = 0

        if not connect_existing:
            if not pathlib.Path(self._config.browser_executable_path).exists():
                raise FileNotFoundError(
                    f"Could not find browser execution at {self._config.browser_executable_path}"
                )

        if getattr(self._config, "_extensions", None):
            self._config.add_argument(
                "--load-extension=%s"
                % ",".join(str(_) for _ in self._config._extensions)
            )

        # 0. Automated Localization (Timezone from IP)
        if self._config.stealth and self._config.proxy and not self._config.timezone:
            self._config.timezone = await util.get_timezone_from_ip(self._config.proxy)

        # Local Proxy Forwarding
        resolved_proxy = None
        if self._config.proxy:
            from . import local_proxy
            self._local_proxy = local_proxy.LocalAuthProxy(self._config.proxy)
            local_port = await self._local_proxy.start()
            resolved_proxy = f"127.0.0.1:{local_port}"

        exe = self._config.browser_executable_path
        params = self._config()
        
        if resolved_proxy:
            for i, p in enumerate(params):
                if p.startswith("--proxy-server="):
                    params[i] = f"--proxy-server={resolved_proxy}"
                    break
            else:
                params.append(f"--proxy-server={resolved_proxy}")

        params.append("about:blank")

        if not connect_existing:
            self._process = util._start_process(exe, params, is_posix)
            self._process_pid = self._process.pid
            # Register immediately to ensure cleanup if crash happens during startup
            util.get_registered_instances().add(self)

            # Robust Port Discovery
            # We read stderr AND check DevToolsActivePort file to find the port if we asked for port 0
            if self._config.port == 0:
                found_port = None

                # Setup DevToolsActivePort file check
                user_data_dir = pathlib.Path(self.config.user_data_dir)
                port_file = user_data_dir / "DevToolsActivePort"

                # Function to read lines with timeout
                async def detect_port_stderr():
                    nonlocal found_port
                    if self._process.stderr is None:
                        return

                    loop = asyncio.get_running_loop()
                    try:
                        # Read line by line but yield back to event loop to allow file check to win
                        while self._process.poll() is None and found_port is None:
                            try:
                                line = await loop.run_in_executor(None, self._process.stderr.readline)
                                if not line:
                                    break

                                line_str = line.decode('utf-8', errors='ignore')

                                # Log stderr for debugging if needed
                                if logger.isEnabledFor(logging.DEBUG):
                                    logger.debug(f"Chrome stderr: {line_str.strip()}")

                                # Look for "DevTools listening on ws://127.0.0.1:12345/..."
                                match = re.search(r'DevTools listening on ws://.+:(\d+)/', line_str)
                                if match:
                                    found_port = int(match.group(1))
                                    logger.info(f"Discovered Chrome DevTools port via stderr: {found_port}")
                                    return
                            except Exception as e:
                                logger.debug(f"Error reading Chrome stderr: {e}")
                                break
                    except Exception as e:
                         logger.debug(f"Stderr reader exception: {e}")

                async def detect_port_file():
                    nonlocal found_port
                    while self._process.poll() is None and found_port is None:
                        if port_file.exists():
                            try:
                                content = port_file.read_text().strip()
                                lines = content.split('\n')
                                if lines and lines[0].isdigit():
                                    found_port = int(lines[0])
                                    logger.info(f"Discovered Chrome DevTools port via file: {found_port}")
                                    return
                            except Exception:
                                pass
                        await asyncio.sleep(0.1)

                try:
                    # Run both detection methods concurrently with a global timeout
                    # Use return_when=asyncio.FIRST_COMPLETED to proceed as soon as one method succeeds
                    done, pending = await asyncio.wait(
                        [asyncio.create_task(detect_port_stderr()), asyncio.create_task(detect_port_file())],
                        timeout=self.config.browser_connection_timeout * 4, # Give it reasonable time (e.g. 10-15s)
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    # Cancel pending tasks to cleanup
                    for task in pending:
                        task.cancel()

                except Exception as e:
                    logger.warning(f"Port discovery exception: {e}")

                if found_port:
                    self._config.port = found_port
                else:
                    logger.error("Could not detect DevTools port from stderr OR file.")
                    # If failed, we check if the process is dead
                    if self._process.poll() is not None:
                         # Read any remaining stderr to help debug
                        remaining_stderr = ""
                        try:
                             if self._process.stderr:
                                 remaining_stderr = self._process.stderr.read().decode('utf-8', errors='ignore')
                        except Exception:
                             pass
                        raise RuntimeError(f"Chrome process died immediately. Return code: {self._process.returncode}. Stderr: {remaining_stderr}")
                    else:
                        # Process is running but no port found?
                        # We should kill it to prevent zombie background processes
                        await self.stop()
                        raise RuntimeError("Timeout waiting for Chrome DevTools port. Process was still running but unresponsive.")

        self._http = HTTPApi((self.config.host, self.config.port))

        # Initial wait for http api
        await asyncio.sleep(self._config.browser_connection_timeout)
        
        for _ in range(self._config.browser_connection_max_tries):
            if await self.test_connection():
                break
            await asyncio.sleep(self._config.browser_connection_timeout)

        if not self.info:
            if self._process is not None:
                # Try to read any remaining stderr
                try:
                    stderr = await util._read_process_stderr(self._process)
                    logger.info("Browser stderr: %s", stderr)
                except Exception:
                    pass
            await self.stop()
            raise Exception("Failed to connect to browser")

        self._connection = Connection(self.info.webSocketDebuggerUrl, _owner=self)

        if self._config.autodiscover_targets:
            self._connection.handlers[cdp.target.TargetInfoChanged] = [self._handle_target_update]
            self._connection.handlers[cdp.target.TargetCreated] = [self._handle_target_update]
            self._connection.handlers[cdp.target.TargetDestroyed] = [self._handle_target_update]
            self._connection.handlers[cdp.target.TargetCrashed] = [self._handle_target_update]
            self._connection.handlers[cdp.target.AttachedToTarget] = [self._handle_attached_to_target]
            
            await self._connection.send(cdp.target.set_discover_targets(discover=True))
            
        await self.update_targets()
        
        for t in self.tabs:
            await self._apply_stealth_and_timezone(t)
            
        return self

    async def test_connection(self) -> bool:
        if not self._http:
            return False
        if self._config.port == 0:
            return False
        try:
            self.info = ContraDict(await self._http.get("version"), silent=True)
            return True
        except Exception:
            return False

    async def stop(self) -> None:
        """Stop the browser instance"""
        if self._connection and not self._connection.closed:
            try:
                await self._connection.send(cdp.browser.close())
            except Exception:
                pass
            try:
                await self._connection.aclose()
            except Exception:
                pass

        if self._process:
            try:
                import sys
                import subprocess
                
                # Force kill on Windows using taskkill to ensure no lingering processes
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(self._process.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    self._process.kill()
                    
                await asyncio.to_thread(self._process.wait)

                # Close Job Object handle on Windows to prevent handle leaks
                if sys.platform == "win32" and hasattr(self._process, "_job_handle"):
                    import ctypes
                    try:
                        ctypes.windll.kernel32.CloseHandle(self._process._job_handle)
                    except Exception:
                        pass
            except Exception:
                # If process is already gone
                pass
            self._process = None
            self._process_pid = None
            
        # Unregister from global list to avoid double cleanup
        util.get_registered_instances().discard(self)

        if self._local_proxy:
            try:
                await self._local_proxy.stop()
            except Exception:
                pass
            self._local_proxy = None

        await self._cleanup_temporary_profile()

    close = stop

    async def _cleanup_temporary_profile(self) -> None:
        if not self.config or self.config.uses_custom_data_dir:
            return

        user_data_path = pathlib.Path(self.config.user_data_dir)
        for attempt in range(10):
            try:
                if user_data_path.exists():
                    shutil.rmtree(self.config.user_data_dir, ignore_errors=False)
                return
            except (PermissionError, OSError):
                await asyncio.sleep(0.1 * (1.5 ** attempt))

    async def __aenter__(self) -> Browser:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.stop()

    def __iter__(self) -> Browser:
        main_tab = self.main_tab
        if not main_tab:
            return self
        self._i = self.tabs.index(main_tab)
        return self

    def __reversed__(self) -> List[Any]:
        return list(reversed(list(self.tabs)))

    def __next__(self) -> Any:
        try:
            res = self.tabs[self._i]
            self._i += 1
            return res
        except (IndexError, AttributeError):
            if hasattr(self, "_i"):
                del self._i
            raise StopIteration


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
        request = urllib.request.Request(url)
        request.method = method
        if data:
            request.data = json.dumps(data).encode("utf-8")

        response = await asyncio.get_running_loop().run_in_executor(
            None, lambda: urllib.request.urlopen(request, timeout=10)
        )
        return json.loads(response.read())
