import asyncio
import pytest
import chuscraper
import logging

# Disable logging for cleaner test output
logging.getLogger("uc").setLevel(logging.ERROR)

@pytest.mark.asyncio
async def test_css_selector_injection_prevented():
    """
    Verifies that JavaScript injection via malicious CSS selectors is prevented.
    This protects against XSS-like vulnerabilities in the JS fallback logic of query_selector.
    """
    # Start browser in headless mode
    async with await chuscraper.start(headless=True) as browser:
        page = browser.main_tab
        await page.goto("about:blank")

        # This selector is designed to break out of backticks in JS fallback:
        # let el = document.querySelector(`${selector}`);
        # If successfully injected, it sets a global variable in the browser.
        malicious_selector = "body` + (window.SENTINEL_VULNERABLE = true) + `"

        try:
            # Attempt to use the malicious selector
            await page.query_selector(malicious_selector)
        except Exception:
            # We expect a ProtocolException or similar because it's invalid CSS for CDP,
            # but we want to ensure the JS fallback also handles it safely.
            pass

        # Check if the injected JS was executed
        is_vulnerable = await page.evaluate("window.SENTINEL_VULNERABLE || false")

        assert is_vulnerable is False, "Vulnerability: JavaScript injection via CSS selector successful!"

@pytest.mark.asyncio
async def test_normal_selector_still_works():
    """
    Ensure that the fix (using json.dumps) doesn't break normal selector functionality.
    """
    async with await chuscraper.start(headless=True) as browser:
        page = browser.main_tab
        await page.goto("about:blank")
        await page.evaluate("document.body.innerHTML = '<div id=\"test\">Sentinel</div>'")

        # Standard selector
        el = await page.query_selector("#test")
        assert el is not None
        # We check tag name instead of text if text extraction has issues in headless/fallback
        assert el.node.node_name.lower() == "div"
