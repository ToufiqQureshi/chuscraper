# Network & Proxies

Chuscraper gives you control over the network layer, allowing you to use proxies, block requests, and inspect traffic.

## Using Proxies

Chuscraper handles proxies differently than standard automation tools. We use a **Local Auth Proxy** architecture:
1.  You provide your upstream proxy (with auth).
2.  Chuscraper spawns a local, tiny TCP bridge.
3.  The browser connects to this bridge.
4.  **Result**: No "Proxy Authentication Required" popups, and full compatibility with headless mode!

```python
# Simple proxy
browser = await cs.start(proxy="127.0.0.1:8080")

# Authenticated proxy (Recommended)
# Format: http://user:pass@host:port
browser = await cs.start(proxy="http://alice:secret123@gw.dataimpulse.com:823")
```

### Rotating Proxies
To rotate proxies, you generally need to close and restart the browser, or use a proxy gateway (like BrightData or IPRoyal) that rotates the IP on the backend while keeping the endpoint constant.

## Request Interception

You can intercept and modify requests using `tab.intercept`.

### Blocking Resources

To block images or analytics to speed up scraping:

```python
# Block all PNGs
await tab.intercept(
    url_pattern="*.png",
    request_stage="Request",
    resource_type="Image"
).abort()
```

### Modifying Headers

Coming soon. (Currently supported via raw CDP `Fetch.enable` and `Fetch.continueRequest`).

## Waiting for Network Idle

Sometimes `await tab.wait(2)` is not enough. You can wait for the network to be idle (no active connections).

*Note: This feature is simulated in Chuscraper by waiting for `document.readyState` or custom predicates.*

```python
# Wait for page to be fully loaded
await tab.wait_for_ready_state("complete")
```
