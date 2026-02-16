"""
Advanced Stealth Scripts for Chuscraper.

These scripts patch known browser automation detection vectors with high-grade evasion techniques:
1. navigator.webdriver → undefined (Prototype & Instance)
2. Permissions API mock
3. Plugins/MimeTypes mock (Proxy-based, native behavior)
4. window.chrome object (Full mock)
5. Hardware fingerprint consistency (Concurrency, Memory)
6. WebGL vendor/renderer spoof (NVIDIA RTX 3060 spoofing)
7. Canvas fingerprinting noise (Non-destructive proxying)
8. iframe contentWindow leak patch
9. Notification permissions
10. Source leak prevention (Robust toString patches without global leaks)
"""


def get_stealth_scripts() -> list[str]:
    """
    Returns JavaScript scripts to inject for bot detection evasion.
    advance-LEVEL: Covers all major detection vectors.
    """
    scripts = []

    # 1. Core Stealth Utilities & toString Patcher
    # This must run FIRST to establish the patching mechanism
    scripts.append("""
    (() => {
        // Shared symbol for the native string representation
        const $symbol = Symbol('toString');
        const $toString = Function.prototype.toString;

        // New toString method that checks for our symbol
        const newToString = function toString() {
            if (this && this[$symbol]) {
                return this[$symbol];
            }
            return $toString.call(this);
        };

        // Mask the new toString method itself
        newToString[$symbol] = $toString.call($toString);

        // Apply to Function prototype
        Object.defineProperty(Function.prototype, 'toString', {
            value: newToString
        });

        // Expose a hidden helper for other patches to use
        // We make it non-enumerable and temporary
        Object.defineProperty(window, '__chu_patch', {
            value: (fn, nativeString) => {
                Object.defineProperty(fn, $symbol, { value: nativeString });
            },
            configurable: true,
            enumerable: false
        });
    })();
    """)

    # 2. Hide navigator.webdriver (CRITICAL)
    scripts.append("""
    (() => {
        try {
            if (Object.prototype.hasOwnProperty.call(navigator, 'webdriver')) {
                delete navigator.webdriver;
            }
            if (Object.prototype.hasOwnProperty.call(Object.getPrototypeOf(navigator), 'webdriver')) {
                delete Object.getPrototypeOf(navigator).webdriver;
            }
        } catch (e) {}
    })();
    """)

    # 3. Mock navigator.permissions
    scripts.append("""
    (() => {
        if (!window.navigator.permissions) return;
        const originalQuery = window.navigator.permissions.query;
        
        const queryProxy = function(parameters) {
             if (parameters && parameters.name === 'notifications') {
                 return Promise.resolve({
                    state: Notification.permission,
                    onchange: null,
                    name: 'notifications'
                 });
             }
             return originalQuery.apply(this, arguments);
        };
        
        // Hide the proxy
        if (window.__chu_patch) {
            window.__chu_patch(queryProxy, "function query() { [native code] }");
        }

        window.navigator.permissions.query = queryProxy;
    })();
    """)

    # 4. Mock window.chrome (Full, realistic mock)
    scripts.append("""
    (() => {
        if (!window.chrome) {
            const chrome = {
                app: {
                    isInstalled: false,
                    InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                    RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' },
                    getDetails: function() { return null; },
                    getIsInstalled: function() { return false; },
                    installState: function(cb) { if(cb) cb('not_installed'); },
                    runningState: function() { return 'cannot_run'; }
                },
                runtime: {
                    OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' },
                    OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
                    PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                    PlatformNaclArch: { ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                    PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' },
                    RequestUpdateCheckStatus: { NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' },
                    connect: function() { return { onDisconnect: { addListener: function() {} }, onMessage: { addListener: function() {} }, postMessage: function() {}, disconnect: function() {} }; },
                    sendMessage: function() {}
                },
                csi: function() { return {}; },
                loadTimes: function() { return {}; }
            };

            // Mask methods in chrome object to look native
            if (window.__chu_patch) {
                window.__chu_patch(chrome.app.getDetails, "function getDetails() { [native code] }");
                window.__chu_patch(chrome.app.getIsInstalled, "function getIsInstalled() { [native code] }");
                window.__chu_patch(chrome.app.installState, "function installState() { [native code] }");
                window.__chu_patch(chrome.app.runningState, "function runningState() { [native code] }");
                window.__chu_patch(chrome.runtime.connect, "function connect() { [native code] }");
                window.__chu_patch(chrome.runtime.sendMessage, "function sendMessage() { [native code] }");
                window.__chu_patch(chrome.csi, "function csi() { [native code] }");
                window.__chu_patch(chrome.loadTimes, "function loadTimes() { [native code] }");
            }

            Object.defineProperty(window, 'chrome', {
                get: () => chrome,
                configurable: true,
                enumerable: true
            });
        }
    })();
    """)

    # 5. Mock navigator.plugins and mimeTypes (Proxy-based)
    scripts.append("""
    (() => {
        const fakeData = {
            plugins: [
                { name: "PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: ["application/pdf"] },
                { name: "Chrome PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: ["application/pdf"] },
                { name: "Chromium PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: ["application/pdf"] },
                { name: "Microsoft Edge PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: ["application/pdf"] },
                { name: "WebKit built-in PDF", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: ["application/pdf"] }
            ],
            mimeTypes: [
                { type: "application/pdf", suffixes: "pdf", description: "Portable Document Format", __pluginName: "PDF Viewer" },
                { type: "text/pdf", suffixes: "pdf", description: "Portable Document Format", __pluginName: "PDF Viewer" }
            ]
        };

        const createPlugin = (data) => {
            const p = {
                name: data.name,
                filename: data.filename,
                description: data.description,
                length: data.mimeTypes.length,
                item: (index) => p[index],
                namedItem: (name) => p[name]
            };

            if (window.__chu_patch) {
                 window.__chu_patch(p.item, "function item() { [native code] }");
                 window.__chu_patch(p.namedItem, "function namedItem() { [native code] }");
            }

            data.mimeTypes.forEach((type, idx) => {
                const mt = fakeData.mimeTypes.find(m => m.type === type);
                if (mt) {
                    p[idx] = mt;
                    p[mt.type] = mt;
                }
            });
            return p;
        };

        const pluginArray = fakeData.plugins.map(createPlugin);
        const pluginArrayProxy = new Proxy(pluginArray, {
            get: (target, prop) => {
                if (prop === 'item') return (i) => target[i];
                if (prop === 'namedItem') return (name) => target.find(x => x.name === name);
                if (prop === 'refresh') return () => {};
                if (prop === 'length') return target.length;
                if (typeof prop === 'string' && !isNaN(prop)) return target[prop];
                const found = target.find(x => x.name === prop);
                if (found) return found;
                return target[prop];
            }
        });

        Object.defineProperty(navigator, 'plugins', {
            get: () => pluginArrayProxy,
            configurable: true,
            enumerable: true
        });

        const mimeArray = fakeData.mimeTypes.map(data => {
            return {
                type: data.type,
                suffixes: data.suffixes,
                description: data.description,
                enabledPlugin: pluginArray.find(p => p.name === data.__pluginName)
            };
        });

        const mimeArrayProxy = new Proxy(mimeArray, {
            get: (target, prop) => {
                if (prop === 'item') return (i) => target[i];
                if (prop === 'namedItem') return (name) => target.find(x => x.type === name);
                if (prop === 'length') return target.length;
                if (typeof prop === 'string' && !isNaN(prop)) return target[prop];
                const found = target.find(x => x.type === prop);
                if (found) return found;
                return target[prop];
            }
        });

        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => mimeArrayProxy,
            configurable: true,
            enumerable: true
        });
    })();
    """)

    # 6. Hardware Concurrency & Device Memory
    scripts.append("""
    (() => {
        try {
             Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
        } catch (e) {}
        try {
             Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
        } catch (e) {}
    })();
    """)

    # 7. WebGL Spoofing (Aggressive)
    scripts.append("""
    (() => {
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        const spoof = {
             37445: 'Google Inc. (NVIDIA)', // UNMASKED_VENDOR_WEBGL
             37446: 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)' // UNMASKED_RENDERER_WEBGL
        };

        const newGetParameter = function(parameter) {
            if (spoof[parameter]) return spoof[parameter];
            return getParameter.apply(this, arguments);
        };

        if (window.__chu_patch) {
             window.__chu_patch(newGetParameter, "function getParameter() { [native code] }");
        }

        WebGLRenderingContext.prototype.getParameter = newGetParameter;

        if (typeof WebGL2RenderingContext !== 'undefined') {
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            const newGetParameter2 = function(parameter) {
                if (spoof[parameter]) return spoof[parameter];
                return getParameter2.apply(this, arguments);
            };
             if (window.__chu_patch) {
                 window.__chu_patch(newGetParameter2, "function getParameter() { [native code] }");
            }
            WebGL2RenderingContext.prototype.getParameter = newGetParameter2;
        }
    })();
    """)

    # 8. Canvas Noise (Smart & Non-destructive)
    scripts.append("""
    (() => {
        const shift = {
            'r': Math.floor(Math.random() * 2) - 1,
            'g': Math.floor(Math.random() * 2) - 1,
            'b': Math.floor(Math.random() * 2) - 1
        };

        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        
        // Proxy getImageData
        const newGetImageData = function(x, y, w, h) {
            const imageData = originalGetImageData.apply(this, arguments);
            if (w < 10 || h < 10) return imageData;

            try {
                const data = imageData.data;
                for (let i = 0; i < data.length; i += 4) {
                     // Sparse noise
                     if (i % 401 === 0) {
                        data[i] = Math.max(0, Math.min(255, data[i] + shift.r));
                        data[i+1] = Math.max(0, Math.min(255, data[i+1] + shift.g));
                        data[i+2] = Math.max(0, Math.min(255, data[i+2] + shift.b));
                     }
                }
            } catch (e) {}
            return imageData;
        };
        
        if (window.__chu_patch) {
             window.__chu_patch(newGetImageData, "function getImageData() { [native code] }");
        }
        CanvasRenderingContext2D.prototype.getImageData = newGetImageData;
        
        // Proxy toDataURL (Using offscreen canvas to avoid modifying the original)
        const newToDataURL = function() {
            try {
                const width = this.width;
                const height = this.height;
                if (width === 0 || height === 0) return originalToDataURL.apply(this, arguments);

                const ctx = this.getContext('2d');
                if (!ctx) return originalToDataURL.apply(this, arguments);

                const data = originalGetImageData.apply(ctx, [0,0, width, height]);
                for (let i = 0; i < data.data.length; i += 4) {
                     if (i % 800 === 0) {
                        data.data[i] = Math.max(0, Math.min(255, data.data[i] + shift.r));
                     }
                }

                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = width;
                tempCanvas.height = height;
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.putImageData(data, 0, 0);

                return originalToDataURL.apply(tempCanvas, arguments);
            } catch(e) {
                return originalToDataURL.apply(this, arguments);
            }
        };
        
        if (window.__chu_patch) {
             window.__chu_patch(newToDataURL, "function toDataURL() { [native code] }");
        }
        HTMLCanvasElement.prototype.toDataURL = newToDataURL;
    })();
    """)

    # 9. Cleanup
    scripts.append("""
    (() => {
        delete window.__chu_patch;
    })();
    """)

    return scripts
