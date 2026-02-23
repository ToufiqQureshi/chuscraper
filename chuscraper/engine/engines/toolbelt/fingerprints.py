from functools import lru_cache
from platform import system as platform_system
from tld import get_tld, Result
from browserforge.headers import Browser, HeaderGenerator
from browserforge.headers.generator import SUPPORTED_OPERATING_SYSTEMS
from chuscraper.engine.core._types import Dict, Literal, Tuple, cast

__OS_NAME__ = platform_system()
OSName = Literal["linux", "macos", "windows"]
chromium_version = 144
chrome_version = 145

@lru_cache(10, typed=True)
def generate_convincing_referer(url: str) -> str | None:
    extracted: Result | None = cast(Result, get_tld(url, as_object=True, fail_silently=True))
    if not extracted: return None
    website_name = extracted.domain
    if not website_name or not extracted.tld or website_name in ("localhost", "127.0.0.1", "::1"): return None
    if all(part.isdigit() for part in website_name.split(".") if part): return None
    return f"https://www.google.com/search?q={website_name}"

@lru_cache(1, typed=True)
def get_os_name() -> OSName | Tuple:
    match __OS_NAME__:
        case "Linux": return "linux"
        case "Darwin": return "macos"
        case "Windows": return "windows"
        case _: return SUPPORTED_OPERATING_SYSTEMS

def generate_headers(browser_mode: bool | str = False, version: int | None = None) -> Dict:
    os_name = get_os_name()
    ver = version if version else (chrome_version if browser_mode and browser_mode == "chrome" else chromium_version)
    browsers = [Browser(name="chrome", min_version=ver, max_version=ver)]
    if not browser_mode:
        os_name = ("windows", "macos", "linux")
        browsers.extend([Browser(name="firefox", min_version=142), Browser(name="edge", min_version=140)])
    return HeaderGenerator(browser=browsers, os=os_name, device="desktop").generate()

__default_useragent__ = generate_headers(browser_mode=False).get("User-Agent")
