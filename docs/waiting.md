# Waiting Strategies

The #1 cause of flaky scrapers is poor waiting logic. Chuscraper provides tools to wait smart, not hard.

## `wait_for` (The Golden Standard)

Always prefer waiting for a specific condition over hard sleeping.

```python
# BAD
await asyncio.sleep(5) 
button = await tab.select("#submit")

# GOOD
# Waits until the element exists in the DOM
button = await tab.wait_for("#submit")
```

## Waiting for State

Sometimes you know an element is there, but you need the page to finish doing something.

### `wait_for_ready_state`
Waits for the basic document lifecycle.
-   `loading`: Standard
-   `interactive`: DOM is parsed.
-   `complete`: Resources (images, etc.) are loaded.

```python
await tab.wait_for_ready_state("complete")
```

## Simulating Human Pauses

If you need to wait to simulate reading time or reaction time, `wait` is your friend. It's an alias for `asyncio.sleep` but reads better.

```python
await tab.wait(2.5)
```

## Handling Timeouts

All wait functions accept a `timeout` argument (default 10s).

```python
try:
    await tab.wait_for("#popup", timeout=5)
except asyncio.TimeoutError:
    print("No popup appeared.")
```
