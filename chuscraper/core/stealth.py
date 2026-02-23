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
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, List

from chuscraper.engine.engines.toolbelt.fingerprints import generate_headers
from chuscraper.engine.engines.toolbelt.navigation import js_bypass_path

if TYPE_CHECKING:
    from chuscraper.core.tab import Tab

logger = logging.getLogger(__name__)

# Default cookie store: ~/.chuscraper/cookies/
COOKIE_DIR = pathlib.Path.home() / ".chuscraper" / "cookies"

# JS Bypass files to load
BYPASS_FILES = [
    "webdriver_fully.js",
    "window_chrome.js",
    "chrome_plugins.js",
    "navigator_hardware.js",
    "navigator_permissions.js",
    "canvas_fingerprint.js",
]

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
    _fingerprint: dict = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self.user_agent or not self._fingerprint:
            # use browserforge to generate a realistic fingerprint
            fp = generate_headers(browser_mode="chrome")
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

    def _build_stealth_script(self) -> str:
        """Loads and compiles advanced JS bypass scripts for stealth."""
        scripts = []
        for filename in BYPASS_FILES:
            try:
                path = js_bypass_path(filename)
                if pathlib.Path(path).exists():
                    with open(path, "r", encoding="utf-8") as f:
                        scripts.append(f.read())
            except Exception as e:
                logger.warning(f"Failed to load bypass script {filename}: {e}")

        # Add configuration variables to scripts
        config_script = f"""
        window._chuscraper_config = {{
            cpu_count: {self.cpu_count},
            device_memory: {self.device_memory},
            screen_width: {self.screen_width},
            screen_height: {self.screen_height},
            user_agent: "{self.user_agent}"
        }};
        """
        scripts.insert(0, config_script)
        return "\n".join(scripts)

    async def apply(self, tab: "Tab", *, load_cookies: bool = True) -> None:
        from chuscraper import cdp
        await tab.send(cdp.page.enable())
        
        # Network level UA override
        await tab.send(cdp.network.set_user_agent_override(user_agent=self.user_agent))

        # JS Injection
        await tab.send(cdp.page.add_script_to_evaluate_on_new_document(source=self._build_stealth_script()))

        # viewport consistency
        await tab.send(cdp.emulation.set_device_metrics_override(
            width=self.screen_width, 
            height=self.screen_height, 
            device_scale_factor=1, 
            mobile=False
        ))
        
        if load_cookies and self.cookie_domain:
            await self.load_cookies(tab)
            
        logger.info(f"Advanced Stealth Applied | {self.screen_width}x{self.screen_height} | UA={self.user_agent}")
