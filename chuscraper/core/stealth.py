"""
stealth.py — Advanced Stealth Engine
============================================
Industry-leading bypass for modern bot managers like Akamai, DataDome, and Cloudflare.
Utilizes browserforge for realistic fingerprinting and advanced JS bypasses.
"""

from __future__ import annotations
import json
import logging
import pathlib
import platform as _platform
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, List, Tuple

from chuscraper.engine.fingerprints import generate_headers

if TYPE_CHECKING:
    from chuscraper.core.tab import Tab

logger = logging.getLogger(__name__)

# Default cookie store: ~/.chuscraper/cookies/
COOKIE_DIR = pathlib.Path.home() / ".chuscraper" / "cookies"

#: where the injected JS bypass files live
BYPASSES_DIR = pathlib.Path(__file__).parent.parent / "engine" / "bypasses"


def js_bypass_path(filename: str) -> str:
    """Absolute path to a bundled JS bypass script."""
    return str(BYPASSES_DIR / filename)


def host_platform() -> Tuple[str, str, str, str]:
    """
    Describe the *real* host OS for Client Hints.

    Returns ``(ua_platform, platform_version, architecture, navigator_platform)``.

    Spoofing "Windows" on a Linux/macOS host is itself a detection signal: the
    UA string, ``navigator.platform`` and ``userAgentData.platform`` all have to
    agree with each other and with things like the font list and WebGL renderer
    that we cannot spoof. So we report the truth about the OS and only randomise
    within it.
    """
    machine = (_platform.machine() or "").lower()
    arch = "arm" if machine in ("arm64", "aarch64", "armv8l", "arm") else "x86"

    if sys.platform == "win32":
        # Chrome reports Windows 11 (and 10) as platformVersion "15.0.0"/"10.0.0"
        release = "15.0.0" if _platform.release() == "11" else "10.0.0"
        return "Windows", release, arch, "Win32"

    if sys.platform == "darwin":
        mac_ver = _platform.mac_ver()[0] or "14.5.0"
        parts = (mac_ver.split(".") + ["0", "0"])[:3]
        return "macOS", ".".join(parts), arch, "MacIntel"

    kernel = (_platform.release() or "6.5.0").split("-")[0]
    nav_platform = "Linux aarch64" if arch == "arm" else "Linux x86_64"
    return "Linux", kernel, arch, nav_platform


# JS Bypass files to load
BYPASS_FILES = [
    "webdriver_fully.js",
    "window_chrome.js",
    "navigator_plugins.js",
    "notification_permission.js",
    "screen_props.js",
    "playwright_fingerprint.js",
    "canvas_webgl_noise.js",
    "iframe_leaks.js",
]

#: stealth_options key -> bypass file it enables/disables
BYPASS_TOGGLES = {
    "webdriver_fully.js": "patch_webdriver",
    "window_chrome.js": "patch_chrome_runtime",
    "navigator_plugins.js": "patch_plugins",
    "notification_permission.js": "patch_notifications",
    "screen_props.js": "patch_screen",
    "playwright_fingerprint.js": "patch_playwright",
    "canvas_webgl_noise.js": "patch_canvas",
    "iframe_leaks.js": "patch_iframe",
}

@dataclass
class SystemProfile:
    """Advanced profile for bypassing high-security bot protection."""
    screen_width: int = 1920
    screen_height: int = 1080
    user_agent: str = ""
    cpu_count: int = 8
    device_memory: int = 8
    extra_headers: dict = field(default_factory=dict)
    cookie_domain: str = ""
    cookie_dir: pathlib.Path = field(default_factory=lambda: COOKIE_DIR)
    browser_version: int = 0
    full_browser_version: str = ""
    stealth_options: dict = field(default_factory=dict)
    #: browser chrome (tab strip + URL bar) and OS taskbar eat into the screen
    browser_chrome_height: int = 139
    taskbar_height: int = 48
    _fingerprint: dict = field(default_factory=dict, repr=False)

    @property
    def viewport_width(self) -> int:
        """Usable viewport width - matches screen width on desktop Chrome."""
        return self.screen_width

    @property
    def viewport_height(self) -> int:
        """Usable viewport height, i.e. screen minus browser chrome and taskbar."""
        return max(
            self.screen_height - self.browser_chrome_height - self.taskbar_height,
            200,
        )

    def __post_init__(self) -> None:
        if not self.user_agent or not self._fingerprint:
            # use browserforge to generate a realistic fingerprint
            fp = generate_headers(browser_mode="chrome", version=self.browser_version or None)
            self.user_agent = fp.get("User-Agent", self.user_agent)
            self._fingerprint = fp
            # update headers
            self.extra_headers.update(fp)

    @classmethod
    def from_system(cls, *, cookie_domain: str = "", **kwargs) -> "SystemProfile":
        """Generates a randomized but standard profile using browserforge."""
        fp = generate_headers(browser_mode="chrome")
        return cls(
            user_agent=fp.get("User-Agent"),
            cookie_domain=cookie_domain,
            _fingerprint=fp,
            **kwargs
        )

    async def save_cookies(self, tab: "Tab") -> int:
        try:
            raw = await tab.get_cookies()
            data = [c if isinstance(c, dict) else c.to_json() for c in raw]
            self.cookie_dir.mkdir(parents=True, exist_ok=True)
            domain_safe = self.cookie_domain.replace(".", "_") or "default"
            path = self.cookie_dir / f"{domain_safe}.json"
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            return len(data)
        except Exception: return 0

    async def load_cookies(self, tab: "Tab") -> int:
        domain_safe = self.cookie_domain.replace(".", "_") or "default"
        path = self.cookie_dir / f"{domain_safe}.json"
        if not path.exists(): return 0
        try:
            with open(path) as f: saved = json.load(f)
            for c in saved:
                try: await tab.set_cookie(**c)
                except: pass
            return len(saved)
        except Exception: return 0

    def _build_config_script(self) -> str:
        """Profile values the bypass scripts read (json.dumps -> no injection)."""
        return "window._chuscraper_config = %s;" % json.dumps({
            "cpu_count": self.cpu_count,
            "device_memory": self.device_memory,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "user_agent": self.user_agent,
        })

    def _build_stealth_script(self, detected_version: int = 145, full_version: str = "145.0.0.0") -> str:
        """
        Loads and compiles advanced JS bypass scripts for stealth as one blob.

        Prefer :py:meth:`_build_stealth_scripts`, which injects each bypass
        separately so a broken one can't take the rest down with it. Kept for
        backwards compatibility.
        """
        return "\n".join(self._build_stealth_scripts(detected_version, full_version))

    def _build_hints_script(self, detected_version: int = 145, full_version: str = "145.0.0.0") -> str:
        """Client Hints + navigator.platform patch, synced to the real host OS."""
        ua_platform, platform_version, architecture, nav_platform = host_platform()

        # Manual Client Hints spoofing to ensure perfect sync.
        # Everything user-controlled goes through json.dumps so a quote or
        # backslash in a UA string can't break out and kill the whole script.
        hints_script = """
        (function() {
            const brands = [
                {brand: "Not:A-Brand", version: %(ver)s},
                {brand: "Chromium", version: %(ver)s},
                {brand: "Google Chrome", version: %(ver)s}
            ];
            brands[0].version = "99";
            const uaData = {
                brands: brands,
                mobile: false,
                platform: %(platform)s
            };

            // Probe with getOwnPropertyDescriptor: reading
            // Navigator.prototype.userAgentData directly invokes the getter on
            // the prototype, which throws "Illegal invocation" and killed this
            // entire script before it applied anything.
            const desc = Object.getOwnPropertyDescriptor(Navigator.prototype, 'userAgentData');
            if (desc) {
                Object.defineProperty(Navigator.prototype, 'userAgentData', {
                    configurable: true,
                    enumerable: desc.enumerable,
                    get: () => ({
                        ...uaData,
                        getHighEntropyValues: async (hints) => ({
                            ...uaData,
                            architecture: %(arch)s,
                            bitness: "64",
                            model: "",
                            platformVersion: %(platform_version)s,
                            uaFullVersion: %(full_version)s,
                            fullVersionList: brands
                        }),
                        toJSON: () => uaData
                    })
                });
            }

            // navigator.platform must agree with userAgentData.platform.
            try {
                Object.defineProperty(Navigator.prototype, 'platform', {
                    configurable: true,
                    get: () => %(nav_platform)s
                });
            } catch (e) {}
        })();
        """ % {
            "ver": json.dumps(str(detected_version)),
            "platform": json.dumps(ua_platform),
            "platform_version": json.dumps(platform_version),
            "arch": json.dumps(architecture),
            "full_version": json.dumps(str(full_version)),
            "nav_platform": json.dumps(nav_platform),
        }
        return hints_script

    def _build_stealth_scripts(self, detected_version: int = 145, full_version: str = "145.0.0.0") -> List[str]:
        """
        The stealth payload as separate scripts, one per bypass.

        A JS *parse* error cannot be caught at runtime, so concatenating every
        bypass into a single script meant one malformed file silently disabled
        all the others (exactly what happened with webdriver_fully.js). Injecting
        them individually contains the blast radius to the broken file.

        The first entry carries the config object and the client-hints patch, so
        later scripts can rely on ``window._chuscraper_config`` existing.
        """
        opts = self.stealth_options
        scripts: List[str] = [
            self._build_config_script() + "\n" + self._build_hints_script(detected_version, full_version)
        ]

        for filename in BYPASS_FILES:
            # Each toggle maps to the file it actually controls (screen_props
            # used to be gated on `patch_canvas`, which is unrelated).
            if opts.get(BYPASS_TOGGLES.get(filename, "")) is False:
                continue
            try:
                path = js_bypass_path(filename)
                if pathlib.Path(path).exists():
                    with open(path, "r", encoding="utf-8") as f:
                        scripts.append(f.read())
                else:
                    logger.warning(f"Bypass script missing from package: {filename}")
            except Exception as e:
                logger.warning(f"Failed to load bypass script {filename}: {e}")
        return scripts

    async def apply(self, tab: "Tab", *, load_cookies: bool = True) -> None:
        from chuscraper import cdp
        
        full_version = await tab.get_browser_version(full=True)
        detected_version = int(full_version.split('.')[0]) if isinstance(full_version, str) else full_version
        
        # If we detected a version, ensure the profile is synced to it.
        # This prevents mismatch between Spoofed UA (144) and Real Kernel (145).
        if detected_version and self.browser_version != detected_version:
            logger.info(f"Syncing Stealth Engine Version: {self.browser_version} -> {detected_version}")
            self.browser_version = detected_version
            self.full_browser_version = full_version
            # Regenerate fingerprint with the actual kernel version
            fp = generate_headers(browser_mode="chrome", version=detected_version)
            self.user_agent = fp.get("User-Agent")
            self._fingerprint = fp
            self.extra_headers.update(fp)
        else:
            self.full_browser_version = full_version

        await tab.send(cdp.page.enable())

        # Construction of UserAgentMetadata for Client Hints sync.
        # Platform/arch come from the *real* host: claiming Windows on a Linux
        # box contradicts the UA string and the un-spoofable signals (fonts,
        # WebGL renderer), which is a detection tell rather than a bypass.
        ua_platform, platform_version, architecture, _nav_platform = host_platform()
        brands = [
            cdp.emulation.UserAgentBrandVersion(brand="Not:A-Brand", version="99"),
            cdp.emulation.UserAgentBrandVersion(brand="Chromium", version=str(self.browser_version)),
            cdp.emulation.UserAgentBrandVersion(brand="Google Chrome", version=str(self.browser_version)),
        ]
        ua_metadata = cdp.emulation.UserAgentMetadata(
            brands=brands,
            full_version_list=brands,
            full_version=self.full_browser_version,
            platform=ua_platform,
            platform_version=platform_version,
            architecture=architecture,
            model="",
            mobile=False,
            bitness="64",
            wow64=False
        )

        # Apply dual-layer CDP override (Network for headers, Emulation for JS/Navigator/Workers)
        # 1. Network level for outgoing headers
        await tab.send(cdp.network.set_user_agent_override(
            user_agent=self.user_agent,
            user_agent_metadata=ua_metadata
        ))
        
        # 2. Emulation level for navigator.userAgent, navigator.appVersion and navigator.userAgentData
        await tab.send(cdp.emulation.set_user_agent_override(
            user_agent=self.user_agent,
            user_agent_metadata=ua_metadata
        ))

        # JS Injection for deeper spoofing (shadowing properties that CDP might
        # miss). One call per bypass so a single broken script can't silently
        # disable all the others.
        for source in self._build_stealth_scripts(self.browser_version, self.full_browser_version):
            try:
                await tab.send(cdp.page.add_script_to_evaluate_on_new_document(source=source))
            except Exception as e:
                logger.warning(f"Failed to inject a stealth bypass script: {e}")

        # Viewport consistency. A real browser's viewport is *smaller* than the
        # screen - tab strip, URL bar, OS taskbar all take space. Setting the
        # viewport equal to the screen makes window.outerHeight === innerHeight,
        # which is one of the oldest headless tells there is.
        await tab.send(cdp.emulation.set_device_metrics_override(
            width=self.viewport_width,
            height=self.viewport_height,
            device_scale_factor=1,
            mobile=False
        ))
        
        if load_cookies and self.cookie_domain:
            await self.load_cookies(tab)
            
        logger.info(f"Advanced Stealth Applied | {self.screen_width}x{self.screen_height} | UA={self.user_agent}")
