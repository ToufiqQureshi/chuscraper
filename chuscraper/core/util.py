from __future__ import annotations

import asyncio
import logging
import subprocess
import types
import typing
from asyncio import AbstractEventLoop
from pathlib import Path
from typing import Any, Callable, List, Optional, Set, Union
import sys

from deprecated import deprecated

if typing.TYPE_CHECKING:
    from .browser import Browser
    from .element import Element
    from .config import PathLike
    from .tab import Tab
from .. import cdp
from .config import BrowserType, Config
from .process import start_process, read_process_stderr, register_browser_cleanup

__registered__instances__: Set[Browser] = set()

logger = logging.getLogger(__name__)
T = typing.TypeVar("T")

register_browser_cleanup(__registered__instances__)




async def start(
    config: Optional[Config] = None,
    *,
    user_data_dir: Optional[PathLike] = None,
    headless: Optional[bool] = False,
    browser_executable_path: Optional[PathLike] = None,
    browser: BrowserType = "auto",
    browser_args: Optional[List[str]] = None,
    sandbox: Optional[bool] = True,
    lang: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    user_agent: Optional[str] = None,
    proxy: Optional[str] = None,
    timezone: Optional[str] = None,
    logging: Optional[bool] = False,
    retry_enabled: Optional[bool] = False,
    retry_timeout: Optional[float] = 10.0,
    retry_count: Optional[int] = 3,
    disable_webrtc: Optional[bool] = True,
    disable_webgl: Optional[bool] = False,
    browser_connection_timeout: Optional[float] = 0.25,
    browser_connection_max_tries: Optional[int] = 10,
    stealth: bool = False,
    stealth_domain: str = "",
    **kwargs: Any,
) -> Browser:
    """
    helper function to launch a browser. it accepts several keyword parameters.
    conveniently, you can just call it bare (no parameters) to quickly launch an instance
    with best practice defaults.
    note: this should be called ```await start()```

    :param user_data_dir:

    :param headless:

    :param browser_executable_path:

    :param browser_args: ["--some-chromeparam=somevalue", "some-other-param=someval"]

    :param sandbox: default True, but when set to False it adds --no-sandbox to the params, also
    when using linux under a root user, it adds False automatically (else chrome won't start

    :param lang: language string

    :param port: if you connect to an existing debuggable session, you can specify the port here
                 if both host and port are provided, chuscraper will not start a local chrome browser!

    :param host: if you connect to an existing debuggable session, you can specify the host here
                 if both host and port are provided, chuscraper will not start a local chrome browser!

    :param expert:  when set to True, enabled "expert" mode.
                    This conveys, the inclusion of parameters: --disable-web-security ----disable-site-isolation-trials,
                    as well as some scripts and patching useful for debugging (for example, ensuring shadow-root is always in "open" mode)

    :param user_agent: if set, this will be used as the user agent for the browser.

    :return:
    """
    if not config:
        config = Config(
            user_data_dir,
            headless,
            browser_executable_path,
            browser,
            browser_args,
            sandbox,
            lang,
            host=host,
            port=port,
            user_agent=user_agent,
            proxy=proxy,
            timezone=timezone,
            logging=logging,
            retry_enabled=retry_enabled,
            retry_timeout=retry_timeout,
            retry_count=retry_count,
            disable_webrtc=disable_webrtc,
            disable_webgl=disable_webgl,
            browser_connection_timeout=browser_connection_timeout,
            browser_connection_max_tries=browser_connection_max_tries,
            **kwargs,
        )
    from .browser import Browser

    browser = await Browser.create(config)

    # ── Stealth mode: auto-apply system fingerprint to the main tab ──────────
    if stealth:
        from .stealth import SystemProfile
        profile = SystemProfile.from_system(cookie_domain=stealth_domain)
        tab = browser.main_tab
        await profile.apply(tab, load_cookies=bool(stealth_domain))
        # Attach profile to browser for later use (e.g., save_cookies)
        browser._stealth_profile = profile

    return browser


async def create_from_undetected_chromedriver(driver: Any) -> Browser:
    """
    create a chuscraper.Browser instance from a running undetected_chromedriver.Chrome instance.
    """
    from .config import Config

    conf = Config()

    host, port = driver.options.debugger_address.split(":")
    conf.host, conf.port = host, int(port)

    # create chuscraper Browser instance
    browser = await start(conf)

    browser._process_pid = driver.browser_pid
    # stop chromedriver binary
    driver.service.stop()
    driver.browser_pid = -1
    driver.user_data_dir = None
    return browser


def get_registered_instances() -> Set[Browser]:
    return __registered__instances__


def free_port() -> int:
    """
    Determines a free port using sockets.
    """
    import socket
    import time
    import random

    free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free_socket.bind(("127.0.0.1", 0))
    free_socket.listen(5)
    port: int = free_socket.getsockname()[1]
    free_socket.close()
    
    # Add a small random delay to desynchronize multiple processes asking for ports simultaneously
    time.sleep(random.uniform(0.01, 0.05))
    return port


def filter_recurse_all(
    doc: T, predicate: Union[Callable[[cdp.dom.Node], bool], Callable[['Element'], bool]]
) -> List[T]:
    """
    test each child using predicate(child), and return all children for which predicate(child) == True

    :param doc: the cdp.dom.Node object or :py:class:`chuscraper.Element`
    :param predicate: a function which takes a node as first parameter and returns a boolean, where True means include
    :return:
    :rtype:
    """
    if not hasattr(doc, "children"):
        raise TypeError("object should have a .children attribute")
    out = []
    if doc and doc.children:
        for child in doc.children:
            if predicate(child):
                # if predicate is True
                out.append(child)
            if child.shadow_roots is not None:
                out.extend(filter_recurse_all(child.shadow_roots[0], predicate))
            out.extend(filter_recurse_all(child, predicate))

    return out


def filter_recurse(
    doc: cdp.dom.Node, predicate: Callable[[cdp.dom.Node], bool]
) -> cdp.dom.Node | None:
    """
    test each child using predicate(child), and return the first child of which predicate(child) == True

    :param doc: the cdp.dom.Node object or :py:class:`chuscraper.Element`
    :param predicate: a function which takes a node as first parameter and returns a boolean, where True means include

    """
    if not hasattr(doc, "children"):
        raise TypeError("object should have a .children attribute")

    if doc and doc.children:
        for child in doc.children:
            if predicate(child):
                # if predicate is True
                return child
            if child.shadow_roots:
                shadow_root_result = filter_recurse(child.shadow_roots[0], predicate)
                if shadow_root_result:
                    return shadow_root_result
            result = filter_recurse(child, predicate)
            if result:
                return result

    return None


def circle(
    x: float, y: float | None = None, radius: int = 10, num: int = 10, dir: int = 0
) -> typing.Generator[typing.Tuple[float, float], None, None]:
    """
    a generator will calculate coordinates around a circle.

    :param x: start x position
    :param y: start y position
    :param radius: size of the circle
    :param num: the amount of points calculated (higher => slower, more cpu, but more detailed)
    :return:
    :rtype:
    """
    import math

    r = radius
    w = num
    if not y:
        y = x
    a = int(x - r * 2)
    b = int(y - r * 2)
    m = (2 * math.pi) / w
    if dir == 0:
        # regular direction
        ran = 0, w + 1, 1
    else:
        # opposite ?
        ran = w + 1, 0, -1

    for i in range(*ran):
        x = a + r * math.sin(m * i)
        y = b + r * math.cos(m * i)

        yield x, y


def remove_from_tree(tree: cdp.dom.Node, node: cdp.dom.Node) -> cdp.dom.Node:
    if not hasattr(tree, "children"):
        raise TypeError("object should have a .children attribute")

    if tree and tree.children:
        for child in tree.children:
            if child.backend_node_id == node.backend_node_id:
                tree.children.remove(child)
            remove_from_tree(child, node)
    return tree


async def html_from_tree(
    tree: Union[cdp.dom.Node, 'Element'], target: 'Tab'
) -> str:
    if not hasattr(tree, "children"):
        raise TypeError("object should have a .children attribute")
    out = ""
    if tree and tree.children:
        for child in tree.children:
            from .element import Element
            if isinstance(child, Element):
                out += await child.get_html()
            elif isinstance(child, cdp.dom.Node):
                out += await target.send(
                    cdp.dom.get_outer_html(backend_node_id=child.backend_node_id)
                )
            else:
                out += child

            if not isinstance(child, str):
                out += await html_from_tree(child, target)
    return out


def compare_target_info(
    info1: cdp.target.TargetInfo | None, info2: cdp.target.TargetInfo
) -> List[typing.Tuple[str, typing.Any, typing.Any]]:
    """
    when logging mode is set to debug, browser object will log when target info
    is changed. To provide more meaningful log messages, this function is called to
    check what has actually changed between the 2 (by simple dict comparison).
    it returns a list of tuples [ ... ( key_which_has_changed, old_value, new_value) ]

    :param info1:
    :param info2:
    :return:
    :rtype:
    """
    d1 = info1.__dict__ if info1 else {}
    d2 = info2.__dict__
    return [(k, v, d2[k]) for (k, v) in d1.items() if d2[k] != v]


@deprecated(
    version="0.5.1", reason="Use asyncio functions directly instead, e.g. asyncio.run"
)
def loop() -> AbstractEventLoop:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def cdp_get_module(domain: Union[str, types.ModuleType]) -> Any:
    """
    get cdp module by given string

    :param domain:
    :return:
    :rtype:
    """
    import importlib

    if isinstance(domain, types.ModuleType):
        # you get what you ask for
        domain_mod = domain
    else:
        try:
            if domain in ("input",):
                domain = "input_"

            #  fallback if someone passes a str
            domain_mod = getattr(cdp, domain)
            if not domain_mod:
                raise AttributeError
        except AttributeError:
            try:
                domain_mod = importlib.import_module(domain)
            except ModuleNotFoundError:
                raise ModuleNotFoundError(
                    "could not find cdp module from input '%s'" % domain
                )
    return domain_mod


def _start_process(
    exe: str | Path, params: List[str], is_posix: bool
) -> subprocess.Popen[bytes]:
    """Compatibility wrapper around modular process launcher."""
    return start_process(exe, params, is_posix)


async def _read_process_stderr(process: subprocess.Popen[bytes], n: int = 2**16) -> str:
    """Compatibility wrapper around modular stderr reader."""
    return await read_process_stderr(process, n)

async def get_timezone_from_ip(proxy: Optional[str] = None) -> Optional[str]:
    """
    Attempts to get the timezone for the given proxy/IP address using ipapi.co.
    """
    import urllib.request
    import json
    import ssl

    url = "https://ipapi.co/timezone/"
    
    # Simple retry logic
    for _ in range(2):
        try:
            # We use urllib to keep dependencies low, but need to handle proxies
            handlers = []
            if proxy:
                # Reconstruct proxy for urllib
                # Assuming http://user:pass@host:port or http://host:port
                handlers.append(urllib.request.ProxyHandler({'https': proxy, 'http': proxy}))
            
            # Disable certificate verification if needed for some proxies, but usually risky.
            # Here we keep it standard.
            opener = urllib.request.build_opener(*handlers)
            # Add User-Agent to keep ipapi happy
            opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
            
            def do_request():
                with opener.open(url, timeout=5) as resp:
                    return resp.read().decode('utf-8').strip()

            tz = await asyncio.to_thread(do_request)
            if tz and "/" in tz:
                # Modernize timezone names
                if tz == "Asia/Calcutta":
                    tz = "Asia/Kolkata"
                elif tz == "Europe/Kiev":
                    tz = "Europe/Kyiv"

                logger.info(f"Detected timezone from IP: {tz}")
                return tz
        except Exception as e:
            logger.debug(f"Failed to fetch timezone from IP: {e}")
            await asyncio.sleep(1)
            
    return None

async def scrape(
    url: str,
    formats: List[str] = ["markdown"],
    stealth: bool = True,
    wait: float = 2.0,
    **kwargs: Any
) -> dict[str, Any]:
    """
    High-level convenience function to scrape a single URL and return structured data.
    Automatically handles browser lifecycle and stealth.

    :param url: The URL to scrape.
    :param formats: List of formats to return ("markdown", "text", "html").
    :param stealth: Whether to enable elite stealth mode (default: True).
    :param wait: Seconds to wait for dynamic content to render.
    :param kwargs: Additional arguments for chuscraper.start()
    :return: A dictionary containing the extracted data.
    """
    from .tab import Tab

    async with await start(stealth=stealth, **kwargs) as browser:
        tab = await browser.get(url)
        if wait > 0:
            await tab.sleep(wait)

        data = {
            "url": tab.url,
            "title": await tab.title(),
            "status": 200 # Inferred if we reached here
        }

        if "markdown" in formats:
            data["markdown"] = await tab.to_markdown()
        if "text" in formats:
            data["text"] = await tab.to_text()
        if "html" in formats:
            data["html"] = await tab.get_content()

        return data
