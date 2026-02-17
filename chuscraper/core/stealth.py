import random
from dataclasses import dataclass, field
from typing import List, Optional

"""
2026 Next-Gen Stealth Hardening for Chuscraper.

This module provides high-entropy evasion scripts designed to pass CreepJS, 
BrowserScan, and Akamai/Cloudflare 2026 benchmarks.

Focus areas:
1. Robust Prototype-based overrides (harder to delete).
2. WebGPU/WebGL depth spoofing.
3. Runtime & Worker Leak Prevention.
4. Intelligent Input Humanization (Preparation for Phase 2).
"""

@dataclass
class StealthProfile:
    vendor: str = "Google Inc. (NVIDIA)"
    renderer: str = "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"
    webgpu_name: str = "NVIDIA GeForce RTX 3060"
    cores: int = 8
    memory: int = 8
    platform: str = "Win32"
    user_agent: Optional[str] = None
    screen_width: int = 1920
    screen_height: int = 1080
    color_depth: int = 24

def generate_profile(os_type: str = "windows") -> StealthProfile:
    """Generates a consistent, high-entropy fingerprint profile."""
    if os_type == "windows":
        gpus = [
            ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)", "NVIDIA GeForce RTX 3060"),
            ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)", "NVIDIA GeForce RTX 3070"),
            ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)", "Intel(R) UHD Graphics 630")
        ]
        gpu = random.choice(gpus)
        return StealthProfile(
            vendor=gpu[0], renderer=gpu[1], webgpu_name=gpu[2],
            cores=random.choice([4, 8, 12, 16]),
            memory=random.choice([8, 16, 32]),
            platform="Win32",
            screen_width=1920, screen_height=1080
        )
    elif os_type == "mac":
        return StealthProfile(
            vendor="Apple Inc.",
            renderer="Apple M1",
            webgpu_name="Apple M1",
            cores=8,
            memory=16,
            platform="MacIntel",
            screen_width=2560, screen_height=1600
        )
    # Default to windows-like
    return generate_profile("windows")

def validate_profile(profile: StealthProfile) -> List[str]:
    """Validates fingerprint consistency."""
    warnings = []
    if "NVIDIA" in profile.renderer and profile.platform == "MacIntel":
        warnings.append("Inconsistency: NVIDIA GPU on MacIntel platform (rare)")
    if profile.cores > 64:
        warnings.append("Inconsistency: Unusually high hardwareConcurrency")
    return warnings

def get_stealth_scripts(profile: Optional[StealthProfile] = None) -> list[str]:
    if not profile:
        profile = StealthProfile()

    scripts = []

    # 1. THE FOUNDATION: Bulletproof toString & Patcher
    # Uses Proxies and hidden Symbols to ensure patches look 100% native.
    # Compatible with Workers (using globalThis).
    scripts.append("""
    (() => {
        const globalScope = globalThis;
        const $toString = Function.prototype.toString;
        const $symbol = Symbol('chu_stealth');

        const chuPatch = (fn, nativeString) => {
            Object.defineProperty(fn, $symbol, {
                value: nativeString,
                configurable: true
            });
        };

        const toStringProxy = new Proxy($toString, {
            apply: (target, thisArg, args) => {
                if (thisArg && thisArg[$symbol]) {
                    return thisArg[$symbol];
                }
                return Reflect.apply(target, thisArg, args);
            }
        });

        chuPatch(toStringProxy, "function toString() { [native code] }");

        // Lock down Function.prototype.toString
        Object.defineProperty(Function.prototype, 'toString', {
            value: toStringProxy,
            configurable: true,
            writable: true
        });

        globalScope.__chu_patch = chuPatch;
    })();
    """)

    # 2. HARDWARE & PLATFORM HARDENING (Prototype Level)
    # Patches Navigator and Screen prototypes.
    scripts.append(f"""
    (() => {{
        const globalScope = globalThis;
        const patchProp = (obj, prop, value) => {{
            Object.defineProperty(obj, prop, {{
                get: () => value,
                set: (v) => {{}}, // Ignore writes
                configurable: false,
                enumerable: true
            }});
        }};

        // Navigator Hardening
        if (globalScope.Navigator) {{
            patchProp(Navigator.prototype, 'webdriver', undefined);
            patchProp(Navigator.prototype, 'hardwareConcurrency', {profile.cores});
            patchProp(Navigator.prototype, 'deviceMemory', {profile.memory});
            patchProp(Navigator.prototype, 'maxTouchPoints', 0);
            patchProp(Navigator.prototype, 'platform', '{profile.platform}');
        }}

        // Screen Hardening (Window only)
        if (globalScope.Screen) {{
            patchProp(Screen.prototype, 'colorDepth', {profile.color_depth});
            patchProp(Screen.prototype, 'pixelDepth', {profile.color_depth});
            patchProp(Screen.prototype, 'width', {profile.screen_width});
            patchProp(Screen.prototype, 'height', {profile.screen_height});
        }}
    }})();
    """)

    # 3. WebGL & WebGPU DEEP SPOOFING (NVIDIA RTX 3060)
    # Works in Workers (OffscreenCanvas).
    scripts.append(f"""
    (() => {{
        const globalScope = globalThis;
        const spoof = {{
            37445: '{profile.vendor}', // UNMASKED_VENDOR_WEBGL
            37446: '{profile.renderer}' // UNMASKED_RENDERER_WEBGL
        }};

        const patchWebGL = (proto) => {{
            const originalGetParameter = proto.getParameter;
            const newGetParameter = function(param) {{
                if (spoof[param]) return spoof[param];
                return Reflect.apply(originalGetParameter, this, arguments);
            }};
            if (globalScope.__chu_patch) globalScope.__chu_patch(newGetParameter, "function getParameter() {{ [native code] }}");
            proto.getParameter = newGetParameter;
        }};

        if (globalScope.WebGLRenderingContext) patchWebGL(WebGLRenderingContext.prototype);
        if (globalScope.WebGL2RenderingContext) patchWebGL(WebGL2RenderingContext.prototype);

        // WebGPU Hardening (2026 standard)
        if (globalScope.GPU && GPU.prototype.requestAdapter) {{
            const originalRequestAdapter = GPU.prototype.requestAdapter;
            const newRequestAdapter = async function() {{
                const adapter = await Reflect.apply(originalRequestAdapter, this, arguments);
                if (!adapter) return null;

                // Proxy the adapter to spoof limits (make them look like a high-end card)
                return new Proxy(adapter, {{
                    get: (target, prop) => {{
                        if (prop === 'name') return '{profile.webgpu_name}';
                        return target[prop];
                    }}
                }});
            }};
            if (globalScope.__chu_patch) globalScope.__chu_patch(newRequestAdapter, "function requestAdapter() {{ [native code] }}");
            GPU.prototype.requestAdapter = newRequestAdapter;
        }}
    }})();
    """)

    # 4. CHROME OBJECT & RUNTIME GUARD
    scripts.append("""
    (() => {
        const globalScope = globalThis;
        // Mock globalThis.chrome if missing (Headless check)
        if (!globalScope.chrome) {
            globalScope.chrome = {
                app: {
                    isInstalled: false,
                    InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                    RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' },
                },
                runtime: {
                    OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' },
                    OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
                    PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                    PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' },
                    sendMessage: () => {},
                    connect: () => ({ onMessage: { addListener: () => {} }, onDisconnect: { addListener: () => {} }, postMessage: () => {}, disconnect: () => {} }),
                },
                csi: () => ({ startE: Date.now(), onloadT: Date.now() + 100, pageT: 50, tran: 15 }),
                loadTimes: () => ({ requestTime: Date.now()/1000, startLoadTime: Date.now()/1000, commitLoadTime: Date.now()/1000 + 0.1, finishDocumentLoadTime: Date.now()/1000 + 0.2, finishLoadTime: Date.now()/1000 + 0.3, firstPaintTime: Date.now()/1000 + 0.15, firstPaintAfterLoadTime: 0, navigationType: 'Other', wasFetchedFromCache: false, wasAlternateProtocolAvailable: false, wasFirstProtocolFromCache: false })
            };
            if (globalScope.__chu_patch) {
                globalScope.__chu_patch(globalScope.chrome.csi, "function csi() { [native code] }");
                globalScope.__chu_patch(globalScope.chrome.loadTimes, "function loadTimes() { [native code] }");
                globalScope.__chu_patch(globalScope.chrome.runtime.sendMessage, "function sendMessage() { [native code] }");
                globalScope.__chu_patch(globalScope.chrome.runtime.connect, "function connect() { [native code] }");
            }
        }

        // Runtime Guard: Detect CDP evaluation and hide it
        const originalError = Error;
        const newError = function() {
            const err = new originalError(...arguments);
            const originalStack = err.stack;
            
            // If stack contains CDP evaluation markers, clean them
            if (originalStack && originalStack.includes('at <anonymous>:')) {
                Object.defineProperty(err, 'stack', {
                    get: () => originalStack.split('\\n').filter(l => !l.includes('<anonymous>:')).join('\\n')
                });
            }
            return err;
        };
        newError.prototype = originalError.prototype;
        globalScope.Error = newError;
    })();
    """)

    # 5. CLEANUP
    scripts.append("""
    (() => {
        const globalScope = globalThis;
        delete globalScope.__chu_patch;
    })();
    """)

    return scripts
