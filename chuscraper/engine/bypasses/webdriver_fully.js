// Hide navigator.webdriver.
//
// This whole file used to be a JavaScript syntax error:
//
//     const nativeGetter = function get webdriver() { ... }
//
// `function get name()` is not valid syntax, so the script failed to parse and
// *none* of it ran - navigator.webdriver stayed true in every session. That
// made this the single most impactful stealth bug in the library, and it was
// invisible because a parse failure in an injected script is silent.
//
// The getter is now built normally and then given the name/toString of a native
// accessor, which is what the original was trying to achieve.
(function () {
    try {
        const nativeGetter = function () {
            return false;
        };

        Object.defineProperties(nativeGetter, {
            name: { value: 'get webdriver', configurable: true },
            length: { value: 0, configurable: true },
            toString: {
                value: function () {
                    return 'function get webdriver() { [native code] }';
                },
                configurable: true,
                writable: true,
            },
        });

        Object.defineProperty(Navigator.prototype, 'webdriver', {
            get: nativeGetter,
            set: undefined,
            enumerable: true,
            configurable: true,
        });

        // Some builds also expose it as an own property on the instance, which
        // would shadow the prototype accessor we just installed.
        if (Object.getOwnPropertyDescriptor(navigator, 'webdriver')) {
            delete navigator.webdriver;
        }
    } catch (e) {
        console.warn(e);
    }
})();
