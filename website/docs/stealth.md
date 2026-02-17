# Stealth & Anti-Detect

Chuscraper is designed to be undetectable by modern bot protection systems like Cloudflare, Akamai, and Datadome.

## Enabling Stealth

Stealth is enabled by creating a `Config` with `stealth=True` or passing it to `start`.

```python
# The easiest way
browser = await cs.start(stealth=True)
```

## How it works

When stealth is enabled, Chuscraper applies a series of patches to the browser environment **before** any page loads.

1.  **Navigator Patching**: Removes `webdriver` property, spoofs `hardwareConcurrency`, `deviceMemory`, `platform`, and `languages`.
2.  **User Agent coherence**: Ensures the `User-Agent` HTTP header matches the `navigator.userAgent` and Client Hints.
3.  **WebGL Spoofing**: Masks the GPU vendor and renderer (often Google SwiftShader in headless) to look like a real GPU (e.g. Nvidia/Intel).
4.  **Runtime Patching**: Emulates `chrome.runtime` presence to look like a regular Chrome instance.
5.  **ToString Patching**: Modifies `Function.prototype.toString` so patched functions return `function name() { [native code] }`.

## Customizing Stealth

You can granularly control which patches are applied via `stealth_options`.

```python
config = cs.Config(stealth=True)
config.stealth_options = {
    "patch_webdriver": True,
    "patch_webgl": False,  # Disable WebGL patching if it causes issues
    "patch_fonts": True,
    # ...
}
browser = await cs.start(config)
```

## Validation

You can test your stealth score on sites like:
-   [CreepJS](https://abrahamjuliot.github.io/creepjs/)
-   [SannySoft](https://bot.sannysoft.com/)
-   [BrowserLeaks](https://browserleaks.com/)

Chuscraper aims for a high trust score on these benchmarks.
