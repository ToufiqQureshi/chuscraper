from pathlib import Path
from functools import lru_cache
from urllib.parse import urlparse
from playwright.async_api import Route as async_Route
from msgspec import Struct, structs, convert, ValidationError
from playwright.sync_api import Route
from chuscraper.engine.core.utils import log
from chuscraper.engine.core._types import Dict, Set, Tuple, Optional, Callable
from chuscraper.engine.engines.constants import EXTRA_RESOURCES

__BYPASSES_DIR__ = Path(__file__).parent / "bypasses"

class ProxyDict(Struct):
    server: str
    username: str = ""
    password: str = ""

def create_intercept_handler(disable_resources: bool, blocked_domains: Optional[Set[str]] = None) -> Callable:
    disabled_resources = EXTRA_RESOURCES if disable_resources else set()
    domains = blocked_domains or set()
    def handler(route: Route):
        if route.request.resource_type in disabled_resources: route.abort()
        elif domains:
            hostname = urlparse(route.request.url).hostname or ""
            if any(hostname == d or hostname.endswith("." + d) for d in domains): route.abort()
            else: route.continue_()
        else: route.continue_()
    return handler

def create_async_intercept_handler(disable_resources: bool, blocked_domains: Optional[Set[str]] = None) -> Callable:
    disabled_resources = EXTRA_RESOURCES if disable_resources else set()
    domains = blocked_domains or set()
    async def handler(route: async_Route):
        if route.request.resource_type in disabled_resources: await route.abort()
        elif domains:
            hostname = urlparse(route.request.url).hostname or ""
            if any(hostname == d or hostname.endswith("." + d) for d in domains): await route.abort()
            else: await route.continue_()
        else: await route.continue_()
    return handler

def construct_proxy_dict(proxy_string: str | Dict[str, str] | Tuple) -> Dict:
    if isinstance(proxy_string, str):
        proxy = urlparse(proxy_string)
        if proxy.scheme not in ("http", "https", "socks4", "socks5") or not proxy.hostname: raise ValueError("Invalid proxy")
        res = {"server": f"{proxy.scheme}://{proxy.hostname}", "username": proxy.username or "", "password": proxy.password or ""}
        if proxy.port: res["server"] += f":{proxy.port}"
        return res
    elif isinstance(proxy_string, dict):
        validated = convert(proxy_string, ProxyDict)
        return structs.asdict(validated)
    raise TypeError(f"Invalid proxy: {proxy_string}")

@lru_cache(10, typed=True)
def js_bypass_path(filename: str) -> str: return str(__BYPASSES_DIR__ / filename)
