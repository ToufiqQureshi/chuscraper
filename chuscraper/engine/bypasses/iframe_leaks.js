// iframe leak bypass.
//
// Also advertised in the README with no implementation behind it.
//
// Detectors create a same-origin (usually about:blank or srcdoc) iframe and
// read navigator/window off `iframe.contentWindow`. Add-script-on-new-document
// patches do not always reach those child realms, so the iframe reports the
// un-patched truth - webdriver flags, missing window.chrome, the real
// navigator.platform - while the top frame looks clean. That disagreement
// between frames is the actual signal.
//
// Fix: intercept contentWindow/contentDocument access and re-apply the top
// frame's patched descriptors to the child realm before handing it over.
(function () {
    try {
        const PATCHED = ['webdriver', 'platform', 'userAgentData', 'plugins', 'languages'];

        const syncRealm = (win) => {
            if (!win || win.__chu_synced) return win;
            try {
                // Only same-origin realms are reachable; cross-origin access
                // throws and there is nothing to leak there anyway.
                void win.document;
            } catch (e) {
                return win;
            }

            try {
                win.__chu_synced = true;

                // Carry over the top frame's patched navigator descriptors.
                for (const prop of PATCHED) {
                    const desc = Object.getOwnPropertyDescriptor(Navigator.prototype, prop);
                    if (desc && win.Navigator) {
                        try {
                            Object.defineProperty(win.Navigator.prototype, prop, desc);
                        } catch (e) {}
                    }
                }

                // window.chrome is absent in fresh child realms even when the
                // top frame has it.
                if (window.chrome && !win.chrome) {
                    try {
                        Object.defineProperty(win, 'chrome', {
                            configurable: true,
                            enumerable: true,
                            get: () => window.chrome,
                        });
                    } catch (e) {}
                }

                // Child realms are a favourite place to fish out a pristine
                // toString / Function reference to compare against ours.
                if (window._chuscraper_config) {
                    try { win._chuscraper_config = window._chuscraper_config; } catch (e) {}
                }
            } catch (e) {}
            return win;
        };

        const patchAccessor = (proto, prop, pick) => {
            const desc = Object.getOwnPropertyDescriptor(proto, prop);
            if (!desc || !desc.get) return;
            Object.defineProperty(proto, prop, {
                configurable: true,
                enumerable: desc.enumerable,
                get: function () {
                    const value = desc.get.call(this);
                    try { syncRealm(pick(value)); } catch (e) {}
                    return value;
                },
            });
        };

        patchAccessor(HTMLIFrameElement.prototype, 'contentWindow', (w) => w);
        patchAccessor(HTMLIFrameElement.prototype, 'contentDocument', (d) => d && d.defaultView);

        // Frames created and read synchronously can dodge the accessors above,
        // so sweep anything already in the document too.
        const sweep = () => {
            try {
                for (const frame of document.querySelectorAll('iframe')) {
                    try { syncRealm(frame.contentWindow); } catch (e) {}
                }
            } catch (e) {}
        };
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', sweep, { once: true });
        } else {
            sweep();
        }
        new MutationObserver(sweep).observe(document.documentElement || document, {
            childList: true,
            subtree: true,
        });
    } catch (e) {
        console.warn(e);
    }
})();
