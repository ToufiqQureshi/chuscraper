import ctypes
import logging
import os
import pathlib
import secrets
import sys
import tempfile
import zipfile
from typing import Any, List, Literal, Optional, Union

__all__ = [
    "Config",
    "find_executable",
    "temp_profile_dir",
    "is_root",
    "is_posix",
    "PathLike",
]

logger = logging.getLogger(__name__)
is_posix = sys.platform.startswith(("darwin", "cygwin", "linux", "linux2"))

PathLike = Union[str, pathlib.Path]
AUTO = None

BrowserType = Literal["chrome", "brave", "auto"]



class Config:
    """
    Config object
    """

    def __init__(
        self,
        user_data_dir: Optional[PathLike] = AUTO,
        headless: Optional[bool] = False,
        browser_executable_path: Optional[PathLike] = AUTO,
        browser: BrowserType = "auto",
        browser_args: Optional[List[str]] = AUTO,
        sandbox: Optional[bool] = True,
        lang: Optional[str] = None,
        host: str | None = AUTO,
        port: int | None = AUTO,
        expert: bool | None = AUTO,
        browser_connection_timeout: float = 0.25,
        browser_connection_max_tries: int = 10,
        user_agent: Optional[str] = None,
        disable_webrtc: Optional[bool] = True,
        disable_webgl: Optional[bool] = False,
        proxy: Optional[str] = None,
        stealth: Optional[bool] = False,
        timezone: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        creates a config object.
        Can be called without any arguments to generate a best-practice config, which is recommended.

        calling the object, eg :  myconfig() , will return the list of arguments which
        are provided to the browser.

        additional arguments can be added using the :py:obj:`~add_argument method`

        Instances of this class are usually not instantiated by end users.

        :param user_data_dir: the data directory to use (must be unique if using multiple browsers)
        :param headless: set to True for headless mode
        :param browser_executable_path: specify browser executable, instead of using autodetect
        :param browser: which browser to use. Can be "chrome", "brave" or "auto". Default is "auto".
        :param browser_args: forwarded to browser executable. eg : ["--some-chromeparam=somevalue", "some-other-param=someval"]
        :param sandbox: disables sandbox
        :param lang: language string to use other than the default "en-US,en;q=0.9"
        :param user_agent: custom user-agent string
        :param expert: when set to True, enabled "expert" mode.
               This conveys, the inclusion of parameters: --disable-web-security ----disable-site-isolation-trials,
               as well as some scripts and patching useful for debugging (for example, ensuring shadow-root is always in "open" mode)

        :param kwargs:
        """

        if not browser_args:
            browser_args = []

        # defer creating a temp user data dir until the browser requests it so
        # config can be used/reused as a template for multiple browser instances
        self._user_data_dir: str | None = None
        self._custom_data_dir = False
        if user_data_dir:
            self.user_data_dir = str(user_data_dir)

        if not browser_executable_path:
            browser_executable_path = find_executable(browser)

        self._browser_args = browser_args
        self.browser_executable_path = browser_executable_path
        self.headless = headless
        self.sandbox = sandbox
        
        # User Agent Rotation
        if not user_agent and stealth:
            # If stealth is on and no UA provided, pick a random modern desktop UA
            # This prevents the default "HeadlessChrome" or "Automation" UA leaks
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            ]
            self.user_agent = secrets.choice(user_agents)
            logger.debug(f"Rotated User-Agent to: {self.user_agent}")
        else:
            self.user_agent = user_agent
        self.host = host
        self.port = port
        self.expert = expert
        self.disable_webrtc = disable_webrtc
        self.disable_webgl = disable_webgl
        self._extensions: list[PathLike] = []
        
        self.proxy = proxy
        self.stealth = stealth
        self.timezone = timezone
        
        if self.proxy:
            import urllib.parse
            # parse proxy string
            # format: scheme://user:pass@host:port or host:port
            if "://" not in self.proxy:
                self.proxy = "http://" + self.proxy
                
            # We no longer create the extension. 
            # We rely on --proxy-server (added below) and CDP Fetch.authRequired (in browser.py)
            # This mimics Playwright and avoids extension detection/issues.
            logger.info(f"Configured proxy: {self.proxy} (Auth handled via CDP)")

        # when using posix-ish operating system and running as root
        # you must use no_sandbox = True, which in case is corrected here
        if is_posix and is_root() and sandbox:
            logger.info("detected root usage, auto disabling sandbox mode")
            self.sandbox = False

        self.autodiscover_targets = True
        self.lang = lang

        self.browser_connection_timeout = browser_connection_timeout
        self.browser_connection_max_tries = browser_connection_max_tries

        # other keyword args will be accessible by attribute
        self.__dict__.update(kwargs)
        super().__init__()
        self._default_browser_args = [
            "--remote-allow-origins=*",
            "--no-first-run",
            "--no-service-autorun",
            "--no-default-browser-check",
            "--homepage=about:blank",
            "--no-pings",
            "--password-store=basic",
            "--disable-infobars",
            "--disable-breakpad",
            "--disable-component-update",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-background-networking",
            "--disable-dev-shm-usage",
            "--disable-features=IsolateOrigins,DisableLoadExtensionCommandLineSwitch,site-per-process",
            "--disable-session-crashed-bubble",
            "--disable-search-engine-choice-screen",
        ]

    @property
    def browser_args(self) -> List[str]:
        return sorted(self._default_browser_args + self._browser_args)

    @property
    def user_data_dir(self) -> str:
        """
        Get the user data dir or lazily create a new one if unset.

        Returns:
            str: User data directory (used for Chrome profile)
        """
        if not self._user_data_dir:
            self._user_data_dir = temp_profile_dir()
            self._custom_data_dir = False

        return self._user_data_dir

    @user_data_dir.setter
    def user_data_dir(self, path: PathLike) -> None:
        if path:
            self._user_data_dir = str(path)
            self._custom_data_dir = True
        else:
            self._user_data_dir = None
            self._custom_data_dir = False

    @property
    def uses_custom_data_dir(self) -> bool:
        return self._custom_data_dir

    def add_extension(self, extension_path: PathLike) -> None:
        """
        adds an extension to load, you could point extension_path
        to a folder (containing the manifest), or extension file (crx)

        :param extension_path:
        :return:
        :rtype:
        """
        path = pathlib.Path(extension_path)

        if not path.exists():
            raise FileNotFoundError("could not find anything here: %s" % str(path))

        if path.is_file():
            tf = tempfile.mkdtemp(prefix="extension_", suffix=secrets.token_hex(4))
            with zipfile.ZipFile(path, "r") as z:
                z.extractall(tf)
                self._extensions.append(tf)

        elif path.is_dir():
            for item in path.rglob("manifest.*"):
                path = item.parent
            self._extensions.append(path)

    # def __getattr__(self, item):
    #     if item not in self.__dict__:

    def __call__(self) -> list[str]:
        # the host and port will be added when starting
        # the browser, as by the time it starts, the port
        # is probably already taken
        args = self._default_browser_args.copy()

        args += ["--user-data-dir=%s" % self.user_data_dir]
        args += ["--disable-features=IsolateOrigins,site-per-process"]
        args += ["--disable-session-crashed-bubble"]
        if self.expert:
            args += ["--disable-web-security", "--disable-site-isolation-trials"]
        if self._browser_args:
            args.extend([arg for arg in self._browser_args if arg not in args])
        if self.headless:
            args.append("--headless=new")
        if self.user_agent:
            args.append(f"--user-agent={self.user_agent}")
        if not self.sandbox:
            args.append("--no-sandbox")
        if self.host:
            args.append("--remote-debugging-host=%s" % self.host)
        if self.port:
            args.append("--remote-debugging-port=%s" % self.port)
        if self.disable_webrtc:
            args += [
                "--webrtc-ip-handling-policy=disable_non_proxied_udp",
                "--force-webrtc-ip-handling-policy",
            ]
        if self.disable_webgl:
            args += ["--disable-webgl", "--disable-webgl2"]

        if self.proxy:
             # Always add proxy-server arg as a reliable fallback.
             # The extension will handle Auth (onAuthRequired) and can also set settings,
             # but this ensures the browser TRIES to use the proxy from the start.
             import urllib.parse
             parsed = urllib.parse.urlparse(self.proxy)
             
             host = parsed.hostname
             port = parsed.port
             if not port:
                port = 80 if parsed.scheme == "http" else 443
                
             # Construct host:port string
             proxy_address = f"{host}:{port}"
             
             # If it wasn't an auth proxy (no user/pass), we would just use self.proxy
             # But since we parsed it, let's reconstruct clean host:port
             # If original was just host:port, parsed.hostname is None (schemeless) or it works.
             
             if not (parsed.hostname): 
                 # Handle case where user passed "host:port" without scheme
                 # urllib might parse it differently. 
                 # But self.proxy was normalized to start with http:// in __init__ if needed.
                 # Let's rely on self.proxy handling in __init__
                 pass

             # If we have an authenticated proxy, we stripped user:pass for the flag
             # If unauthenticated, it's just the proxy string
             
             # Safest: Re-parse using the logic we know works
             if "://" not in self.proxy:
                  self.proxy = "http://" + self.proxy # Should have been done in init but safe to repeat or check
             
             p = urllib.parse.urlparse(self.proxy)
             if p.hostname:
                 args.append(f"--proxy-server={p.hostname}:{p.port}")

        return args

    def add_argument(self, arg: str) -> None:
        if any(
            x in arg.lower()
            for x in [
                "headless",
                "data-dir",
                "data_dir",
                "no-sandbox",
                "no_sandbox",
                "lang",
            ]
        ):
            raise ValueError(
                '"%s" not allowed. please use one of the attributes of the Config object to set it'
                % arg
            )
        self._browser_args.append(arg)

    def __repr__(self) -> str:
        s = f"{self.__class__.__name__}"
        for k, v in ({**self.__dict__, **self.__class__.__dict__}).items():
            if k[0] == "_":
                continue
            if not v:
                continue
            if isinstance(v, property):
                v = getattr(self, k)
            if callable(v):
                continue
            s += f"\n\t{k} = {v}"
        return s

    #     d = self.__dict__.copy()
    #     d.pop("browser_args")
    #     d["browser_args"] = self()
    #     return d


def is_root() -> bool:
    """
    helper function to determine if user trying to launch chrome
    under linux as root, which needs some alternative handling
    :return:
    :rtype:
    """
    if sys.platform == "win32":
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    else:
        return os.getuid() == 0


def temp_profile_dir() -> str:
    """generate a temp dir (path)"""
    path = os.path.normpath(tempfile.mkdtemp(prefix="uc_"))
    return path


def find_binary(candidates: list[str]) -> str | None:
    rv: list[str] = []
    for candidate in candidates:
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            logger.debug("%s is a valid candidate... " % candidate)
            rv.append(candidate)
        else:
            logger.debug(
                "%s is not a valid candidate because don't exist or not executable "
                % candidate
            )

    winner: str | None = None
    if rv and len(rv) > 1:
        # assuming the shortest path wins
        winner = min(rv, key=lambda x: len(x))

    elif len(rv) == 1:
        winner = rv[0]

    return winner


def find_executable(browser: BrowserType = "auto") -> PathLike:
    """
    Finds the executable for the specified browser and returns its disk path.
    :param browser: The browser to find. Can be "chrome", "brave" or "auto".
    :return: The path to the browser executable.
    """
    browsers_to_try = []
    if browser == "auto":
        browsers_to_try = ["chrome", "brave"]
    elif browser in ["chrome", "brave"]:
        browsers_to_try = [browser]
    else:
        raise ValueError("browser must be 'chrome', 'brave' or 'auto'")

    for browser_name in browsers_to_try:
        candidates = []
        if browser_name == "chrome":
            if is_posix:
                for item in os.environ["PATH"].split(os.pathsep):
                    for subitem in (
                        "google-chrome",
                        "chromium",
                        "chromium-browser",
                        "chrome",
                        "google-chrome-stable",
                    ):
                        candidates.append(os.sep.join((item, subitem)))
                if "darwin" in sys.platform:
                    candidates += [
                        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                        "/Applications/Chromium.app/Contents/MacOS/Chromium",
                    ]
            else:
                for item2 in map(
                    os.environ.get,
                    (
                        "PROGRAMFILES",
                        "PROGRAMFILES(X86)",
                        "LOCALAPPDATA",
                        "PROGRAMW6432",
                    ),
                ):
                    if item2 is not None:
                        for subitem in (
                            "Google/Chrome/Application",
                            "Google/Chrome Beta/Application",
                            "Google/Chrome Canary/Application",
                            "Google/Chrome SxS/Application",
                        ):
                            candidates.append(
                                os.sep.join((item2, subitem, "chrome.exe"))
                            )
        elif browser_name == "brave":
            if is_posix:
                for item in os.environ["PATH"].split(os.pathsep):
                    for subitem in (
                        "brave-browser",
                        "brave",
                    ):
                        candidates.append(os.sep.join((item, subitem)))
                if "darwin" in sys.platform:
                    candidates.append(
                        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
                    )
            else:
                for item2 in map(
                    os.environ.get,
                    ("PROGRAMFILES", "PROGRAMFILES(X86)"),
                ):
                    if item2 is not None:
                        for subitem in ("BraveSoftware/Brave-Browser/Application",):
                            candidates.append(
                                os.sep.join((item2, subitem, "brave.exe"))
                            )
        winner = find_binary(candidates)
        if winner:
            return os.path.normpath(winner)

    raise FileNotFoundError(
        "could not find a valid browser binary. please make sure it is installed "
        "or use the keyword argument 'browser_executable_path=/path/to/your/browser' "
    )
