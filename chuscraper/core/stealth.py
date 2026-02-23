"""
stealth.py — System-Based Browser Fingerprint Engine
======================================================
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import platform
import re
import sys
import time
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from chuscraper.core.tab import Tab

logger = logging.getLogger(__name__)

# Default cookie store: ~/.chuscraper/cookies/
COOKIE_DIR = pathlib.Path.home() / ".chuscraper" / "cookies"


# ──────────────────────────────────────────────────────────────────────────────
#  System Fingerprint Detection
# ──────────────────────────────────────────────────────────────────────────────

def _get_screen_size() -> tuple[int, int]:
    """Read actual monitor resolution from the OS."""
    try:
        if sys.platform == "win32":
            import ctypes
            user32 = ctypes.windll.user32
            w = user32.GetSystemMetrics(0)
            h = user32.GetSystemMetrics(1)
            if w > 0 and h > 0:
                return w, h
    except Exception:
        pass
    return 1920, 1080


def _get_timezone() -> str:
    """Return IANA timezone string from system settings."""
    try:
        if sys.platform == "win32":
            import subprocess
            out = subprocess.check_output(
                ["powershell", "-Command", "[TimeZoneInfo]::Local.Id"],
                stderr=subprocess.DEVNULL, timeout=5
            ).decode().strip()
            _WIN_MAP = {
                "India Standard Time": "Asia/Kolkata",
                "UTC": "UTC",
                "Eastern Standard Time": "America/New_York",
                "Pacific Standard Time": "America/Los_Angeles",
                "Central Standard Time": "America/Chicago",
                "Greenwich Standard Time": "Europe/London",
                "Central European Standard Time": "Europe/Paris",
                "Singapore Standard Time": "Asia/Singapore",
                "China Standard Time": "Asia/Shanghai",
                "Tokyo Standard Time": "Asia/Tokyo",
            }
            if out in _WIN_MAP:
                return _WIN_MAP[out]
    except Exception:
        pass
    offset_hours = -time.timezone // 3600
    if offset_hours == 5:
        return "Asia/Kolkata"
    return "Asia/Kolkata" if offset_hours == 5.5 else "UTC"


def _get_language() -> str:
    try:
        import locale as loc
        lang, _ = loc.getdefaultlocale()
        if lang:
            return lang.replace("_", "-")
    except Exception:
        pass
    return "en-US"


def _get_chrome_version(executable_path: Optional[str] = None) -> str:
    candidates = []
    if executable_path:
        candidates.append(executable_path)
    if sys.platform == "win32":
        for base in (os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", ""), os.environ.get("LOCALAPPDATA", "")):
            if base: candidates.append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))
    else:
        candidates.extend(["/usr/bin/google-chrome", "/usr/bin/chromium-browser"])

    for cand in candidates:
        if not os.path.exists(cand): continue
        try:
            import subprocess
            out = subprocess.check_output([cand, "--version"], stderr=subprocess.DEVNULL, timeout=5).decode().strip()
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", out)
            if m: return m.group(1)
        except Exception: continue
    return "124.0.0.0"


def _get_cpu_count() -> int:
    return os.cpu_count() or 8


def _get_platform_string() -> str:
    return "Win32" if sys.platform == "win32" else "Linux x86_64"


# ──────────────────────────────────────────────────────────────────────────────
#  SystemProfile
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SystemProfile:
    screen_width: int = 1920
    screen_height: int = 1080
    timezone: str = "Asia/Kolkata"
    language: str = "en-US"
    platform: str = "Win32"
    cpu_count: int = 8
    chrome_version: str = "124.0.0.0"
    user_agent: str = ""
    cookie_domain: str = ""
    cookie_dir: pathlib.Path = field(default_factory=lambda: COOKIE_DIR)

    # Noise seeds
    noise_seed_r: int = 0
    noise_seed_g: int = 0
    noise_seed_b: int = 0

    def __post_init__(self) -> None:
        if not self.user_agent:
            self.user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.chrome_version} Safari/537.36"

        # Initialize random noise if zero (default)
        if self.noise_seed_r == 0: self.noise_seed_r = random.randint(-1, 1) or 1
        if self.noise_seed_g == 0: self.noise_seed_g = random.randint(-1, 1) or -1
        if self.noise_seed_b == 0: self.noise_seed_b = random.randint(-1, 1) or 0

    @classmethod
    def from_system(cls, *, cookie_domain: str = "", chrome_executable: Optional[str] = None) -> "SystemProfile":
        w, h = _get_screen_size()
        tz   = _get_timezone()
        lang = _get_language()
        cpu  = _get_cpu_count()
        plat = _get_platform_string()
        cv   = _get_chrome_version(chrome_executable)
        return cls(screen_width=w, screen_height=h, timezone=tz, language=lang, platform=plat, cpu_count=cpu, chrome_version=cv, cookie_domain=cookie_domain)

    @property
    def _cookie_file(self) -> pathlib.Path:
        domain = self.cookie_domain or "default"
        safe = re.sub(r"[^\w\-.]", "_", domain)
        return self.cookie_dir / f"{safe}.json"

    async def save_cookies(self, tab: "Tab") -> int:
        try:
            raw = await tab.get_cookies()
            data = [c if isinstance(c, dict) else c.to_json() for c in raw]
            self.cookie_dir.mkdir(parents=True, exist_ok=True)
            with open(self._cookie_file, "w") as f: json.dump(data, f, indent=2)
            return len(data)
        except Exception: return 0

    async def load_cookies(self, tab: "Tab") -> int:
        if not self._cookie_file.exists(): return 0
        try:
            with open(self._cookie_file) as f: saved = json.load(f)
            injected = 0
            for c in saved:
                try:
                    await tab.set_cookie(name=c["name"], value=c["value"], domain=c.get("domain", f".{self.cookie_domain}"), path=c.get("path", "/"), secure=c.get("secure", False), http_only=c.get("httpOnly", False))
                    injected += 1
                except Exception: pass
            return injected
        except Exception: return 0

    def _build_stealth_script(self) -> str:
        lang = self.language
        lang_short = lang.split("-")[0]

        return f"""
(function() {{
    const NOISE_R = {self.noise_seed_r};
    const NOISE_G = {self.noise_seed_g};
    const NOISE_B = {self.noise_seed_b};

    // ── 1. Webdriver Hardening ──────────────────────────────────────────────
    // Ensure navigator.webdriver is false and deep in prototype
    try {{
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => false,
        }});
    }} catch (e) {{}}

    try {{
        Object.defineProperty(Navigator.prototype, 'webdriver', {{
            get: () => false,
        }});
    }} catch (e) {{}}


    // ── 2. Chrome Runtime ───────────────────────────────────────────────────
    if (!window.chrome) {{
        window.chrome = {{
            runtime: {{}},
            loadTimes: () => ({{}}),
            csi: () => ({{}}),
            app: {{ isInstalled: false }}
        }};
    }}

    // ── 3. Plugins & MimeTypes ──────────────────────────────────────────────
    // Construct fake plugins to match Chrome
    const createPlugin = (data) => {{
        const p = Object.create(Plugin.prototype);
        Object.assign(p, data);
        return p;
    }};
    const pluginData = [
        {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
        {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: 'Google Chrome PDF Viewer' }},
        {{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }}
    ];
    const plugins = pluginData.map(createPlugin);
    
    const pArray = Object.create(PluginArray.prototype);
    plugins.forEach((pl, i) => pArray[i] = pl);
    pArray.length = plugins.length;
    pArray.item = (i) => plugins[i];
    pArray.namedItem = (n) => plugins.find(x => x.name === n);
    pArray.refresh = () => {{}};

    Object.defineProperty(navigator, 'plugins', {{ get: () => pArray }});
    Object.defineProperty(navigator, 'mimeTypes', {{ get: () => Object.create(MimeTypeArray.prototype) }}); // Simplified mime types for now


    // ── 4. Hardware and Memory ───────────────────────────────────────────────
    Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {self.cpu_count}, configurable: true }});
    Object.defineProperty(navigator, 'deviceMemory', {{ get: () => 8, configurable: true }});
    Object.defineProperty(navigator, 'platform', {{ get: () => '{self.platform}', configurable: true }});

    // ── 5. Languages ─────────────────────────────────────────────────────────
    Object.defineProperty(navigator, 'language', {{ get: () => '{lang}', configurable: true }});
    Object.defineProperty(navigator, 'languages', {{ get: () => ['{lang}', '{lang_short}'], configurable: true }});

    // ── 6. Canvas Fingerprint Noise ──────────────────────────────────────────
    // We add slight noise to toDataURL to randomize the fingerprint
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    Object.defineProperty(HTMLCanvasElement.prototype, "toDataURL", {{
        value: function(type, encoderOptions) {{
            // Use temporary canvas to prevent tainting the original
            try {{
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = this.width;
                tempCanvas.height = this.height;
                const ctx = tempCanvas.getContext("2d");

                if (ctx) {{
                    ctx.drawImage(this, 0, 0);
                    const imgData = ctx.getImageData(0, 0, this.width, this.height);
                    const data = imgData.data;

                    // Modifying just one pixel is often enough to change the hash
                    for (let i = 0; i < this.height; i++) {{
                        for (let j = 0; j < this.width; j++) {{
                            const index = ((i * (this.width * 4)) + (j * 4));
                            // Add deterministic noise based on coordinate to avoid flickering
                            if (index % 100 === 0) {{
                                data[index] = data[index] + NOISE_R;
                                data[index+1] = data[index+1] + NOISE_G;
                                data[index+2] = data[index+2] + NOISE_B;
                            }}
                        }}
                    }}
                    ctx.putImageData(imgData, 0, 0);
                    return originalToDataURL.apply(tempCanvas, arguments);
                }}
            }} catch(e) {{
                // If generic error (e.g. tainted canvas), ignore and proceed with original
            }}
            return originalToDataURL.apply(this, arguments);
        }}
    }});

    // Also patch getImageData to be consistent (safe to return modified buffer)
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    Object.defineProperty(CanvasRenderingContext2D.prototype, "getImageData", {{
        value: function(sx, sy, sw, sh) {{
             const imgData = originalGetImageData.apply(this, arguments);
             try {{
                 const data = imgData.data;
                 for (let i = 0; i < data.length; i += 4) {{
                      if (i % 100 === 0) {{
                        data[i] = data[i] + NOISE_R;
                        data[i+1] = data[i+1] + NOISE_G;
                        data[i+2] = data[i+2] + NOISE_B;
                      }}
                 }}
             }} catch (e) {{}}
             return imgData;
        }}
    }});

    // ── 7. WebGL Fingerprint Noise ───────────────────────────────────────────
    const getParameterProxy = (ctx, original, parameter) => {{
        // Mask Vendor/Renderer
        if (parameter === 37445) return 'Google Inc. (NVIDIA)'; // UNMASKED_VENDOR_WEBGL
        if (parameter === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)'; // UNMASKED_RENDERER_WEBGL
        return original.call(ctx, parameter);
    }};

    const wrapWebGL = (contextName) => {{
        const proto = window[contextName].prototype;
        const origGetParam = proto.getParameter;
        Object.defineProperty(proto, "getParameter", {{
            value: function(parameter) {{
                return getParameterProxy(this, origGetParam, parameter);
            }}
        }});
    }};

    if (window.WebGLRenderingContext) wrapWebGL('WebGLRenderingContext');
    if (window.WebGL2RenderingContext) wrapWebGL('WebGL2RenderingContext');


    // ── 8. Permissions ───────────────────────────────────────────────────────
    if (navigator.permissions) {{
        const origQuery = navigator.permissions.query;
        navigator.permissions.query = (q) => (q.name === 'notifications') ?
            Promise.resolve({{ state: Notification.permission, onchange: null }}) : origQuery(q);
    }}

    // ── 9. WebRTC IP Handling ────────────────────────────────────────────────
    // Minimal override to ensure candidate gathering doesn't leak local IP easily
    const origRTC = window.RTCPeerConnection;
    if (origRTC) {{
        window.RTCPeerConnection = function(config) {{
            if (config && !config.iceServers) {{
                 config.iceServers = [{{urls: 'stun:stun.l.google.com:19302'}}];
            }}
            return new origRTC(config);
        }};
        window.RTCPeerConnection.prototype = origRTC.prototype;
    }}

}})();
"""

    async def apply(self, tab: "Tab", *, load_cookies: bool = True) -> None:
        from chuscraper import cdp
        await tab.send(cdp.page.enable())
        await tab.send(cdp.network.enable())
        
        # CRITICAL: Override User-Agent at the network level to match JS
        await tab.send(cdp.network.set_user_agent_override(user_agent=self.user_agent))

        await tab.send(cdp.page.add_script_to_evaluate_on_new_document(source=self._build_stealth_script()))
        await tab.send(cdp.emulation.set_device_metrics_override(width=self.screen_width, height=self.screen_height, device_scale_factor=1, mobile=False))
        
        if self.timezone:
            try: await tab.send(cdp.emulation.set_timezone_override(timezone_id=self.timezone))
            except Exception: pass
            
        if load_cookies and self.cookie_domain:
            await self.load_cookies(tab)
            
        logger.info(f"Stealth Hardened: {self.screen_width}x{self.screen_height} | UA={self.user_agent} | Noise=({self.noise_seed_r},{self.noise_seed_g},{self.noise_seed_b})")
