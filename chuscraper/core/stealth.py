def get_stealth_scripts() -> list[str]:
    """
    Returns a list of JavaScript scripts to be injected for evasion.
    Includes:
    - Navigator webdriver hiding
    - Permissions mocking
    - Plugins/MimeTypes mocking
    - Hardware concurrency/memory spoofing
    - Canvas & WebGL fingerprinting noise
    """
    scripts = []

    # 1. Hide navigator.webdriver
    scripts.append("""
    Object.defineProperty(navigator, 'webdriver', {
      get: () => undefined
    });
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

    # 3. Mock navigator.plugins and mimeTypes (Enhanced)
    scripts.append("""
    (function () {
        const fakePlugins = [
            { name: "PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: [{ type: "application/pdf", suffixes: "pdf" }] },
            { name: "Chrome PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: [{ type: "application/pdf", suffixes: "pdf" }] },
            { name: "Chromium PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: [{ type: "application/pdf", suffixes: "pdf" }] },
            { name: "Microsoft Edge PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: [{ type: "application/pdf", suffixes: "pdf" }] },
            { name: "WebKit built-in PDF", filename: "internal-pdf-viewer", description: "Portable Document Format", mimeTypes: [{ type: "application/pdf", suffixes: "pdf" }] }
        ];
        
        // Lightweight mock - sophisticated bots might check prototypes, but this covers basic checks
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const p = fakePlugins;
                p.item = (i) => p[i];
                p.namedItem = (name) => p.find(x => x.name === name);
                p.refresh = () => {};
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

    # 4. Mock window.chrome
    scripts.append("""
    if (!window.chrome) {
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
    }
    """)
    
    # 5. Hardware Concurrency & Device Memory Spoofing (High-end PC)
    scripts.append("""
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
    """)

    # 6. WebGL Fingerprinting Noise
    scripts.append("""
    (function() {
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // Spoof unmasked vendor/renderer if requested
            if (parameter === 37445) return 'Google Inc. (NVIDIA)'; # UNMASKED_VENDOR_WEBGL
            if (parameter === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)'; # UNMASKED_RENDERER_WEBGL
            return getParameter.apply(this, arguments);
        };
    })();
    """)

    # 7. Canvas Fingerprinting Noise
    scripts.append("""
    (function() {
        const toBlob = HTMLCanvasElement.prototype.toBlob;
        const toDataURL = HTMLCanvasElement.prototype.toDataURL;
        const getImageData = CanvasRenderingContext2D.prototype.getImageData;
        
        // Add random noise to canvas exports
        const noise = () => Math.floor(Math.random() * 10) - 5; # -5 to 5 delta
        
        const smudge = (context, width, height) => {
             // Active Noise Injection
             // Slightly modify one random pixel to alter the canvas hash
             // This is imperceptible to humans but changes the fingerprint
             const imageData = context.getImageData(0, 0, width, height);
             const data = imageData.data;
             
             // Pick a random pixel index (ensure it's within bounds)
             for (let i = 0; i < 2; i++) {
                 const idx = Math.floor(Math.random() * (data.length / 4)) * 4;
                 // Modify Blue channel by +/- 1
                 const noise = Math.random() > 0.5 ? 1 : -1;
                 data[idx + 2] = Math.max(0, Math.min(255, data[idx + 2] + noise));
             }
             
             context.putImageData(imageData, 0, 0);
        };
    })();
    """)

    return scripts
