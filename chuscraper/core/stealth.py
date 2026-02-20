import random
import time
from typing import Any, Optional

from .fingerprint_profiles import get_random_profile, BrowserProfile

"""
senior-level stealth engine designed to pass 2026 bot detection benchmarks.
"""

def get_stealth_scripts(config: Any, browser_version: str | None = None) -> tuple[list[str], BrowserProfile]:
    """
    Generates a list of high-entropy, coherent stealth scripts based on the provided configuration.
    Returns the scripts and the selected profile.

    :param config: The BrowserConfig object.
    :param browser_version: The detected Chrome version (e.g. "124.0.6367.119").
    :return: A tuple of (list of scripts, BrowserProfile used)
    """
    # 1. IDENTIFY DESIRED OS FROM UA OR CONFIG
    ua_input = getattr(config, 'user_agent', '') or ''
    
    # Simple heuristic to guess OS from input UA if present
    os_type = "auto"
    if ua_input:
        if "Windows" in ua_input:
            os_type = "Windows"
        elif "Mac" in ua_input:
            os_type = "macOS"
        elif "Linux" in ua_input:
            os_type = "Linux"

    profile = get_random_profile(os_type)
    
    # 2. RESOLVE CHROME VERSION
    if browser_version:
        chrome_ver_full = browser_version
        chrome_ver_major = browser_version.split('.')[0]
    else:
        # Fallback to recent stable if detection failed
        chrome_ver_major = "124"
        chrome_ver_full = "124.0.6367.119"

    # 3. CONSTRUCT USER AGENT IF NOT PROVIDED
    if ua_input:
        new_ua = ua_input
    else:
        # Construct a coherent UA string using the profile's platform and the actual Chrome version
        new_ua = f"Mozilla/5.0 ({profile.ua_platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver_full} Safari/537.36"
        config.user_agent = new_ua
    
    # Session-persistent seed
    seed = getattr(config, '_stealth_seed', random.randint(1, 1000000))

    scripts = []
    opts = getattr(config, 'stealth_options', {})

    # 1. THE FOUNDATION: Bulletproof toString & Nativization
    scripts.append(f"""
    (() => {{
        const $toString = Function.prototype.toString;
        const $symbol = Symbol('chu_stealth');

        const chuPatch = (fn, nativeString) => {{
            try {{
                Object.defineProperty(fn, $symbol, {{
                    value: nativeString,
                    configurable: true
                }});
            }} catch(e) {{}}
        }};

        const toStringProxy = new Proxy($toString, {{
            apply: (target, thisArg, args) => {{
                if (thisArg && thisArg[$symbol]) {{
                    return thisArg[$symbol];
                }}
                if (thisArg === toStringProxy) {{
                    return "function toString() {{ [native code] }}";
                }}
                return Reflect.apply(target, thisArg, args);
            }}
        }});

        chuPatch(toStringProxy, "function toString() {{ [native code] }}");

        Object.defineProperty(Function.prototype, 'toString', {{
            value: toStringProxy,
            configurable: true,
            writable: true
        }});

        globalThis.__chu_patch = chuPatch;
    }})();
    """)

    # 2. NAVIGATOR & WEBDRIVER
    if opts.get("patch_webdriver", True):
        scripts.append(f"""
        try {{
            const navProto = Navigator.prototype;
            
            const patchProp = (obj, prop, value) => {{
                try {{
                    Object.defineProperty(obj, prop, {{
                        get: () => value,
                        set: (v) => {{}},
                        configurable: true,
                        enumerable: true
                    }});
                }} catch(e) {{}}
            }};

            // Mask WebDriver (Return false, but keep descriptor clean)
            try {{
                Object.defineProperty(navProto, 'webdriver', {{
                    get: () => false,
                    configurable: true,
                    enumerable: true
                }});
                if (globalThis.__chu_patch) {{
                    const desc = Object.getOwnPropertyDescriptor(navProto, 'webdriver');
                    globalThis.__chu_patch(desc.get, "function get webdriver() {{ [native code] }}");
                }}
            }} catch(e) {{}}

            patchProp(navProto, 'hardwareConcurrency', {profile.cores});
            patchProp(navProto, 'deviceMemory', {profile.memory});
            patchProp(navProto, 'maxTouchPoints', 0);
            patchProp(navProto, 'platform', '{profile.platform}');
            patchProp(navProto, 'userAgent', '{new_ua}');
            
            // Client Hints coherence
            if (navProto.userAgentData) {{
                // Detect Windows version from UA string to spoof correct platformVersion
                // Windows 10 -> '10.0.0'
                // Windows 11 -> '15.0.0' (Usually mapped to this in newer Chrome)
                let platformVersion = '';
                if ('{profile.os}' === 'Windows') {{
                    if ('{new_ua}'.includes('Windows NT 10.0')) {{
                        platformVersion = '10.0.0';
                    }} else if ('{new_ua}'.includes('Windows NT 11.0')) {{
                        platformVersion = '15.0.0';
                    }}
                }}

                const data = {{
                    brands: [
                        {{ brand: 'Not(A:Brand', version: '99' }},
                        {{ brand: 'Google Chrome', version: '{chrome_ver_major}' }},
                        {{ brand: 'Chromium', version: '{chrome_ver_major}' }}
                    ],
                    mobile: false,
                    platform: '{profile.os}',
                    ...(platformVersion ? {{ platformVersion: platformVersion }} : {{}})
                }};

                patchProp(navProto, 'userAgentData', data);
            }}
        }} catch(e) {{}}
        """)

    # 3. SCREEN RESOLUTION & VIEWPORT
    # We patch screen.width/height to match our profile
    # Note: Window innerWidth/Height will be set via CDP commands in tab.py usually,
    # but patching screen object properties ensures JS consistency.
    scripts.append(f"""
        try {{
            const screenProto = Screen.prototype;
            const patchProp = (obj, prop, value) => {{
                Object.defineProperty(obj, prop, {{ get: () => value, configurable: true }});
            }};

            patchProp(screenProto, 'width', {profile.screen_width});
            patchProp(screenProto, 'height', {profile.screen_height});
            patchProp(screenProto, 'availWidth', {profile.screen_width});
            patchProp(screenProto, 'availHeight', {profile.screen_height});
            patchProp(screenProto, 'colorDepth', 24);
            patchProp(screenProto, 'pixelDepth', 24);
        }} catch(e) {{}}
    """)

    # 4. WEBGL & GPU
    if opts.get("patch_webgl", True):
        gpu = profile.gpu
        scripts.append(f"""
        try {{
            const spoof = {{
                37445: '{gpu.vendor}', 
                37446: '{gpu.renderer}',
                7936: '{gpu.vendor}', 
                7937: '{gpu.renderer}' 
            }};

            const patchWebGL = (proto) => {{
                const originalGetParameter = proto.getParameter;
                const newGetParameter = function(param) {{
                    if (spoof[param]) return spoof[param];
                    return Reflect.apply(originalGetParameter, this, [param]);
                }};
                if (globalThis.__chu_patch) globalThis.__chu_patch(newGetParameter, "function getParameter() {{ [native code] }}");
                proto.getParameter = newGetParameter;
            }};

            if (globalThis.WebGLRenderingContext) patchWebGL(WebGLRenderingContext.prototype);
            if (globalThis.WebGL2RenderingContext) patchWebGL(WebGL2RenderingContext.prototype);
        }} catch(e) {{}}
        """)

    # 5. CHROME RUNTIME & PLUGINS
    if opts.get("patch_chrome_runtime", True):
        scripts.append("""
        try {
            if (!globalThis.chrome) {
                globalThis.chrome = {
                    app: { 
                        isInstalled: false, 
                        InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }, 
                        RunningState: { CANNOT_RUN: 'cannot_run', RUNNING: 'running', CAN_RUN: 'can_run' },
                        getIsInstalled: () => false,
                        getDetails: () => {}
                    },
                    runtime: {
                        sendMessage: () => {},
                        connect: () => ({ 
                            onMessage: { addListener: () => {}, removeListener: () => {} }, 
                            onDisconnect: { addListener: () => {}, removeListener: () => {} }, 
                            postMessage: () => {}, 
                            disconnect: () => {} 
                        }),
                        OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' },
                        OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
                        PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                        PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' },
                        id: undefined
                    },
                    webstore: {
                        install: () => {},
                        onInstallStageChanged: { addListener: () => {}, removeListener: () => {} },
                        onDownloadProgress: { addListener: () => {}, removeListener: () => {} }
                    },
                    csi: () => ({ startE: Date.now(), onloadT: Date.now() + 100, pageT: 50, tran: 15 }),
                    loadTimes: () => ({ requestTime: Date.now()/1000, startLoadTime: Date.now()/1000, commitLoadTime: Date.now()/1000 + 0.1, navigationType: 'Other' })
                };
                if (globalThis.__chu_patch) {
                    globalThis.__chu_patch(globalThis.chrome.csi, "function csi() { [native code] }");
                    globalThis.__chu_patch(globalThis.chrome.loadTimes, "function loadTimes() { [native code] }");
                }
            }
        } catch(e) {}
        """)

    # 6. CLEANUP GLOBAL PATCHER
    scripts.append("try { delete globalThis.__chu_patch; } catch(e) {}")

    return scripts, profile
