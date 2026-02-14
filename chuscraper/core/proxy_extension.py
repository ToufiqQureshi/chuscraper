"""
PATCHRIGHT-LEVEL Proxy Auth Extension Generator.

Strategy: DUAL proxy enforcement
1. chrome.proxy.settings — Sets proxy at Chrome API level
2. --proxy-server CLI arg — Forces proxy at process level (added by config.py)

Authentication is handled by chrome.webRequest.onAuthRequired with
'blocking' + 'extraHeaders' options for modern Chrome compatibility.

This dual approach ensures:
- No IP leaks (CLI arg prevents direct connection fallback)
- No auth popups (extension handles 407 challenges silently)
- No browser hangs (unlike CDP Fetch.enable approach)
"""

import os
import shutil
import tempfile


def create_proxy_auth_extension(proxy_host, proxy_port, proxy_username, proxy_password, scheme='http'):
    """
    Creates a Chrome extension for proxy authentication.
    
    Uses Manifest V2 for maximum compatibility with webRequestBlocking.
    Sets proxy.settings AND handles onAuthRequired for dual enforcement.
    
    Returns: path to the extension directory
    """
    manifest_json = """{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chuscraper Proxy Auth",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version": "22.0.0"
}"""

    # DUAL enforcement: settings + auth handler
    background_js = f"""
// ============================================
// CHUSCRAPER PROXY - PATCHRIGHT LEVEL
// ============================================

// 1. Set proxy configuration via Chrome API
// This is REDUNDANT with the --proxy-server CLI arg,
// but provides a fallback in case CLI is stripped.
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "{scheme}",
            host: "{proxy_host}",
            port: parseInt({proxy_port})
        }},
        bypassList: ["localhost", "127.0.0.1"]
    }}
}};

chrome.proxy.settings.set(
    {{value: config, scope: "regular"}},
    function() {{
        if (chrome.runtime.lastError) {{
            console.error("Proxy settings error:", chrome.runtime.lastError);
        }}
    }}
);

// 2. Handle 407 Proxy Authentication Required
// Uses 'blocking' + 'extraHeaders' for modern Chrome compatibility
function callbackFn(details) {{
    return {{
        authCredentials: {{
            username: "{proxy_username}",
            password: "{proxy_password}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ['blocking', 'extraHeaders']
);

// 3. Log proxy errors for debugging
chrome.proxy.onProxyError.addListener(function(details) {{
    console.error("Proxy Error:", details.error, details.details, details.fatal);
}});
"""

    # Create extension directory
    plugin_dir = os.path.join(
        tempfile.gettempdir(), 
        f"chuscraper_proxy_{proxy_host}_{proxy_port}"
    )
    
    if os.path.exists(plugin_dir):
        shutil.rmtree(plugin_dir)
    os.makedirs(plugin_dir)

    with open(os.path.join(plugin_dir, "manifest.json"), "w") as f:
        f.write(manifest_json)

    with open(os.path.join(plugin_dir, "background.js"), "w") as f:
        f.write(background_js)

    return plugin_dir
