import random
import time
from typing import Any

from .fingerprint_profiles import get_random_profile, BrowserProfile

"""
senior-level stealth engine designed to pass 2026 bot detection benchmarks.
"""

def get_stealth_scripts(config: Any) -> list[str]:
    """
    Generates a list of high-entropy, coherent stealth scripts based on the provided configuration.
    """
    # 1. IDENTIFY DESIRED OS FROM UA OR CONFIG
    ua_input = getattr(config, 'user_agent', '') or ''
    os_type = "win" if "Windows" in ua_input else ("mac" if "Mac" in ua_input else "auto")
    profile = get_random_profile(os_type)
    
    # Update config.user_agent to match profile for coherence across headers
    # We use a modernized base UA and inject the profile platform
    
    # Use a realistic recent stable version instead of future/invalid versions
    chrome_ver_major = "124"
    chrome_ver_full = "124.0.6367.119"

    if ua_input:
        new_ua = ua_input
    else:
        if profile.os == "Windows":
            new_ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver_full} Safari/537.36"
        else:
            new_ua = f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver_full} Safari/537.36"
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
                const data = {{
                    brands: [
                        {{ brand: 'Not(A:Brand', version: '99' }},
                        {{ brand: 'Google Chrome', version: '{chrome_ver_major}' }},
                        {{ brand: 'Chromium', version: '{chrome_ver_major}' }}
                    ],
                    mobile: false,
                    platform: '{profile.os}'
                }};
                patchProp(navProto, 'userAgentData', data);
            }}
        }} catch(e) {{}}
        """)

    # 3. WEBGL & GPU
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

    # 4. CHROME RUNTIME & PLUGINS
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

    # 5. CLEANUP GLOBAL PATCHER
    scripts.append("try { delete globalThis.__chu_patch; } catch(e) {}")

    return scripts
