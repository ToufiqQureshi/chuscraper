// Keep window/screen geometry self-consistent.
//
// This used to hard-code outerWidth/outerHeight (1313x754) and
// devicePixelRatio: 2, which contradicted both the configured screen size and
// the device_scale_factor=1 we set over CDP. Detectors cross-check these, so a
// mismatch here is worse than not patching at all. Now everything is derived
// from the one profile in window._chuscraper_config.
(function () {
    try {
        const cfg = window._chuscraper_config || {};
        const screenWidth = cfg.screen_width || window.screen.width;
        const screenHeight = cfg.screen_height || window.screen.height;

        // Real desktop Chrome: outer window is the viewport plus browser chrome,
        // and never larger than the screen.
        const outerWidth = Math.min(window.innerWidth || screenWidth, screenWidth);
        const outerHeight = Math.min(
            (window.innerHeight || screenHeight) + 139,
            screenHeight
        );

        const define = (target, prop, value) => {
            try {
                Object.defineProperty(target, prop, {
                    configurable: true,
                    get: () => value,
                });
            } catch (e) {
                /* property is locked down; leaving the native value is safer */
            }
        };

        define(window, 'outerWidth', outerWidth);
        define(window, 'outerHeight', outerHeight);
        define(window, 'screenX', 0);
        define(window, 'screenY', 0);
        // Must match device_scale_factor passed to Emulation.setDeviceMetricsOverride.
        define(window, 'devicePixelRatio', 1);

        define(window.screen, 'width', screenWidth);
        define(window.screen, 'height', screenHeight);
        define(window.screen, 'availWidth', screenWidth);
        // Taskbar/dock shaves some height off the available area.
        define(window.screen, 'availHeight', Math.max(screenHeight - 48, 200));
        define(window.screen, 'colorDepth', 24);
        define(window.screen, 'pixelDepth', 24);
    } catch (e) {
        console.warn(e);
    }
})();
