# Advanced CDP

Chuscraper is built on top of the Chrome DevTools Protocol (CDP). While the `tab` object provides high-level methods, you can always drop down to the raw protocol for advanced use cases.

## Sending Commands

You can send any CDP command using `tab.send(command)`. Returns are typed if you use the `cdp` module.

```python
from chuscraper import cdp

# Enable network domain
await tab.send(cdp.network.enable())

# Clear browser cache
await tab.send(cdp.network.clear_browser_cache())

# Get cookies raw
cookies = await tab.send(cdp.network.get_cookies())
print(cookies)
```

## Listening for Events

To listen for CDP events (like `Network.requestWillBeSent` or `Console.messageAdded`), you can register listeners.

```python
async def on_console(event: cdp.console.MessageAdded):
    print(f"Console: {event.message.text}")

# Register listener
tab.add_handler(cdp.console.MessageAdded, on_console)

# Enable the domain to start receiving events
await tab.send(cdp.console.enable())
```

## Creating Custom Commands

If a CDP command is missing or you want to construct one manually:

```python
# Raw dictionary command
result = await tab.send_raw({
    "method": "Page.reload",
    "params": {"ignoreCache": True}
})
```
