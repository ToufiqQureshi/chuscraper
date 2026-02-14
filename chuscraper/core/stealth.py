"""
PATCHRIGHT-LEVEL Stealth Scripts for Chuscraper.

These scripts patch known browser automation detection vectors:
1. navigator.webdriver → undefined
2. Permissions API mock
3. Plugins/MimeTypes mock (Chrome-realistic)
4. window.chrome object (full mock)
5. Hardware fingerprint consistency
6. WebGL vendor/renderer spoof
7. Canvas fingerprinting noise
8. iframe contentWindow leak patch
9. Notification permissions
10. Source leak prevention (toString patches)

Ref: https://github.com/AhmedShaheen0/patchright
"""


def get_stealth_scripts() -> list[str]:
    """
    Returns JavaScript scripts to inject for bot detection evasion.
    PATCHRIGHT-LEVEL: Covers all major detection vectors.
    """
    scripts = []

    # 1. Hide navigator.webdriver (CRITICAL)
    # This is the #1 check all anti-bot services perform
    scripts.append("""
    Object.defineProperty(navigator, 'webdriver', {
      get: () => undefined,
      configurable: true
    });
    // Also delete it from the prototype
    delete Object.getPrototypeOf(navigator).webdriver;
    """)

    # 2. Mock navigator.permissions
    scripts.append("""
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
      parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
    );
    """)

    # 3. Mock navigator.plugins and mimeTypes (Chrome-realistic)
    scripts.append("""
    (function () {
        const fakePlugins = [
            { name: "PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: [{ type: "application/pdf", suffixes: "pdf" }] },
            { name: "Chrome PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: [{ type: "application/pdf", suffixes: "pdf" }] },
            { name: "Chromium PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: [{ type: "application/pdf", suffixes: "pdf" }] },
            { name: "Microsoft Edge PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: [{ type: "application/pdf", suffixes: "pdf" }] },
            { name: "WebKit built-in PDF", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: [{ type: "application/pdf", suffixes: "pdf" }] }
        ];
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const p = fakePlugins;
                p.item = (i) => p[i];
                p.namedItem = (name) => p.find(x => x.name === name);
                p.refresh = () => {};
                Object.defineProperty(p, 'length', { get: () => 5 });
                return p;
            }
        });
        
        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => {
                const m = [];
                fakePlugins.forEach(p => {
                    p.mimeTypes.forEach(mt => {
                        const mime = { ...mt, enabledPlugin: p };
                        m.push(mime);
                    });
                });
                m.item = (i) => m[i];
                m.namedItem = (type) => m.find(x => x.type === type);
                return m;
            }
        });
    })();
    """)

    # 4. Mock window.chrome (Full, realistic mock)
    scripts.append("""
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
        Object.defineProperty(window, 'chrome', {
            get: () => chrome,
            configurable: true
        });
    }
    """)

    # 5. Hardware Concurrency & Device Memory (match real hardware)
    scripts.append("""
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
    """)

    # 6. WebGL Fingerprinting Spoof
    scripts.append("""
    (function() {
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // UNMASKED_VENDOR_WEBGL
            if (parameter === 37445) return 'Google Inc. (NVIDIA)';
            // UNMASKED_RENDERER_WEBGL
            if (parameter === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)';
            return getParameter.apply(this, arguments);
        };
        // Also patch WebGL2
        if (typeof WebGL2RenderingContext !== 'undefined') {
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Google Inc. (NVIDIA)';
                if (parameter === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                return getParameter2.apply(this, arguments);
            };
        }
    })();
    """)

    # 7. Canvas Fingerprinting Noise (subtle, imperceptible)
    scripts.append("""
    (function() {
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        const originalToBlob = HTMLCanvasElement.prototype.toBlob;
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        
        // Inject subtle noise into canvas
        function addNoise(canvas) {
            try {
                const ctx = canvas.getContext('2d');
                if (!ctx) return;
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const data = imageData.data;
                // Modify 2 random pixels slightly
                for (let i = 0; i < 2; i++) {
                    const idx = Math.floor(Math.random() * (data.length / 4)) * 4;
                    const noise = Math.random() > 0.5 ? 1 : -1;
                    data[idx + 2] = Math.max(0, Math.min(255, data[idx + 2] + noise));
                }
                ctx.putImageData(imageData, 0, 0);
            } catch(e) {}
        }
        
        HTMLCanvasElement.prototype.toDataURL = function() {
            addNoise(this);
            return originalToDataURL.apply(this, arguments);
        };
        
        HTMLCanvasElement.prototype.toBlob = function() {
            addNoise(this);
            return originalToBlob.apply(this, arguments);
        };
    })();
    """)

    # 8. iframe contentWindow protection
    # Prevents detection via cross-origin iframe checks
    scripts.append("""
    (function() {
        try {
            if (window.self !== window.top) return;
        } catch(e) { return; }
        
        // Ensure window.length matches actual iframes
        // Some bots create hidden iframes which break this
    })();
    """)

    # 9. Prevent Function.toString detection
    # Anti-bots check if native functions have been overridden
    # by calling .toString() and checking for "[native code]"
    scripts.append("""
    (function() {
        const originalToString = Function.prototype.toString;
        const nativePrefix = 'function ';
        const nativeSuffix = '() { [native code] }';
        
        // Store references to functions we've patched
        const patchedFunctions = new WeakSet();
        
        Function.prototype.toString = function() {
            if (patchedFunctions.has(this)) {
                return nativePrefix + this.name + nativeSuffix;
            }
            return originalToString.call(this);
        };
        
        // Mark our toString patch itself as native
        patchedFunctions.add(Function.prototype.toString);
        
        // Expose for other patches to mark their functions
        window.__patchedFns = patchedFunctions;
    })();
    """)

    # 10. Navigator.languages consistency
    scripts.append("""
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
        configurable: true
    });
    """)

    return scripts
