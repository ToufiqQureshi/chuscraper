# Changelog

## 0.21.0 — Scope: four pillars

chuscraper is now deliberately four things and nothing else:
**stealth scraping · web automation · mobile (ADB) scraping & automation · AI extraction.**

Everything outside that has been removed or deprecated. Nothing in the four
pillars changed behaviour.

### Removed (dead code, no public API)

- `chuscraper/engine/engines/` — its route-interception handlers were never
  called from anywhere. `js_bypass_path()` (one line) moved into `core/stealth.py`
  and `fingerprints.py` moved up to `chuscraper/engine/`.
- `Browser.tile_windows()` — window tiling; never called, and it raised
  `ZeroDivisionError` with no windows open.

### Deprecated (still works, removed in 0.22)

These stay importable and emit a `DeprecationWarning`:

- `HumanBehavior` (`core.behavior`) — the stealth engine plus
  `click(mode="human")` and `type(..., delay=...)` already cover this. Keeping a
  second implementation is how `mouse_movement_pattern()` stayed a silent no-op.
- `RateLimiter`, `SessionManager` (`core.limiter`) — use `asyncio.Semaphore`, or
  `aiolimiter` for token buckets.
- `Logger`, `FailureDumper` (`core.observability`) — use the stdlib `logging`
  module and handle failure artefacts in your own error path.

`import chuscraper` remains warning-free: deprecated names resolve lazily
through a module `__getattr__`, so you only see a warning if you use one.

### Dependencies: 22 → 15

| Removed | Why |
|---|---|
| **`playwright`** | Never used functionally — only two type hints in the deleted `engines/` subtree, on handlers nothing called. ~50MB plus browser downloads, in every install. |
| `msgspec` | Only used by that same dead file. |
| `mss` | Only used by `tile_windows()`. |
| `curl_cffi` | Declared but never imported anywhere. |
| `psutil` | Only used by the test suite — moved to the dev group. |

(`grapheme` became optional in 0.20.0.)

### Added

- `tests/core/test_scope.py` — guards the scope: fails if a heavy dependency
  returns, if `import chuscraper` starts emitting warnings, if a pillar entry
  point breaks, or if removed helpers come back.

### Repo cleanup

- `verify_17.py` — scratch verification script from an old release.
- `publish.ps1` — three-line `twine upload` wrapper; the publish workflow
  already does this.
- `codecov.yml` — no workflow uploads coverage.
- `tests/Dockerfile`, `tests/next_test.sh` — an interactive VNC test harness
  that no longer runs: it calls `uv sync --frozen` with no `uv.lock` in the
  repo, and its entrypoint is `./scripts/test.sh`, which does not exist.
- CI matrix trimmed from four Python versions to the oldest and newest
  supported (3.10, 3.13), and the `setup-node` step dropped since node is
  preinstalled on `ubuntu-latest`.

## 0.20.0 — Bug sweep

A full pass over the codebase for correctness bugs. Several headline features
were not working at all; this release fixes them.

### Stealth (was substantially broken)

- **`webdriver_fully.js` was a JavaScript syntax error** (`function get webdriver()`),
  so it never parsed and `navigator.webdriver` stayed `true` in every session.
  Because all bypasses were concatenated into a single injected script, this one
  parse error silently disabled **every other bypass too**. Bypasses are now
  injected individually so one bad script cannot take the rest down.
- **`Browser.getVersion` returns a 5-tuple**, but the code read `.product` off it,
  raising `AttributeError` every time. Chrome version auto-detection therefore
  *never* worked and always fell back to a hardcoded `145`, so the spoofed
  User-Agent never matched the real browser build.
- **Client Hints spoofing never applied.** Reading `Navigator.prototype.userAgentData`
  directly throws "Illegal invocation", which killed the whole script.
- **Platform was hardcoded to `"Windows"`** regardless of host OS, contradicting
  the UA string and un-spoofable signals. Now derived from the real host.
- **Viewport was set equal to screen size**, making `outerHeight === innerHeight` —
  a classic headless tell. The viewport is now correctly smaller than the screen.
- `screen_props.js` hardcoded 1313x754 and `devicePixelRatio: 2`, contradicting
  both the configured screen size and the `device_scale_factor=1` sent over CDP.
- Added the Canvas/WebGL noise and iframe-leak bypasses the README advertised
  but which did not exist.
- `stealth_options` toggles now map to the file each one actually controls
  (`screen_props.js` was gated on the unrelated `patch_canvas`).
- User-agent strings are JSON-escaped before being embedded in injected JS.

### Element interaction (was broken for `select()`-found elements)

- **`DOM.resolveNode` was passed a raw `int`** instead of a `BackendNodeId`, so it
  raised `AttributeError` (swallowed by a bare `except`) on every call. As a
  result `apply()` — and everything built on it: `fill()`, `clear_input()`,
  `focus()`, `get_js_attributes()` — failed with "Could not resolve object" for
  any element obtained via `select()` / `query_selector()`.
- `apply()` ignored `exceptionDetails`, so a JS exception in the page was
  reported as a successful call returning the error object.
- `fill()` / `clear_input()` assigned `.value` directly, firing no events, so
  React/Vue/Angular kept their old state. Now uses the native value setter plus
  `input` + `change` events.
- `type()` re-focused the element over a CDP round-trip for *every character*.
- `click(mode="human")` sent no `mouseMoved` before pressing and always hit the
  exact centre. It now approaches the target and varies the landing point.
- `Position` used a duplicate-name tuple unpack that was only correct by
  coincidence for axis-aligned boxes, and wrong for CSS-transformed elements.
- `DOM.setFileInputFiles` was passed both `backendNodeId` and `objectId`; CDP
  accepts exactly one.

### Crawler

- **A synchronous `on_page_crawled` callback silently discarded every page** — it
  was neither invoked nor stored. Total, silent data loss.
- **Concurrency was effectively 1.** Workers exited after a 2s idle-queue timeout,
  so with a 4s page settle every worker but one died before the first page
  produced links. Workers now run until the queue is genuinely drained.
- **Relative links resolved against the origin instead of the page**, so
  `page2.html` on `/docs/` became `/page2.html`. Links containing `#` were
  dropped entirely, relative links without a `/` were dropped, and asset URLs
  (`script`, `link`, `meta`) were queued for navigation.
- `max_pages` could be overshot by up to `concurrency` pages.
- Nested sitemap recursion had no cycle or depth guard.
- `formats=["markdown"]` was a mutable default argument.
- CSV column order was non-deterministic between runs.

### Markdown extraction

- The "remove empty elements" pass deleted any element with no text, taking out
  `<div><img></div>`, image-only links and figures — images included.
- Only the **first** `<article>` was kept, so listing and blog-index pages lost
  nearly all their content.
- On failure it returned `"Error converting to markdown: ..."` *as the page
  content*, so the error string landed in datasets as a real document. It now
  raises `MarkdownConversionError`.
- A stateful `HTML2Text` instance was reused across documents.

### Connection / process stability

- **CDP commands had no timeout and pending futures were never rejected** when the
  socket dropped, so a lost connection hung the caller forever and leaked the
  transaction.
- The `closed` property checked `.closed` then `.open`, neither of which exists on
  `websockets` >= 14, so it reported "closed" for every healthy connection and
  forced a reconnect before every command.
- Chrome's stdout was never drained and stderr was only drained until the port
  line, so a full pipe buffer could block the browser mid-session.
- `remove_handlers(event_type)` raised `KeyError` for an unregistered event type.

### Mobile / ADB

- **`input_text()` was a shell-injection boundary.** `adb shell` joins arguments
  into a device-side shell command and only spaces were escaped, so `;`, `&`,
  `|`, backticks and `$(...)` executed on the device. Text is now quoted safely.
- UI hierarchy dumps went to a timestamped file in the process working
  directory, colliding whenever two dumps happened in the same second.
- `MobileElement.click()` swallowed every failure, so a click that did nothing
  was indistinguishable from one that worked.

### AI extraction

- **The `schema` argument was accepted and completely ignored** by both the OpenAI
  and Ollama extractors. Schemas (JSON Schema dicts or Pydantic models) are now
  enforced via structured outputs, with a prompt-embedded fallback.
- Content truncation is now logged instead of silently dropping the page tail.

### Other

- `wait_for_idle()` did not wait for idle — it slept the full timeout every time.
  It now polls readyState plus in-flight requests and returns as soon as the page
  is quiet.
- `screenshot(full_page=True)` never restored the device-metrics override, leaving
  the viewport stuck at full-page height for the rest of the session.
- `Tab.xpath()` was hard-capped at 100 results with no warning; now configurable
  and it reports truncation.
- Undefined `logger`, `Optional` and `Union` in `core/tabs/storage.py` meant any
  localStorage failure raised `NameError`.
- `Browser` shared a single class-level `asyncio.Lock` across all instances.
- `Browser.start()` read `.returncode` without polling, so a dead browser looked
  alive.
- `tile_windows()` raised `ZeroDivisionError` with no windows open.
- `main_tab` could return a non-page target; `goto()` crashed when it was `None`.
- Duplicate `Tab` objects could be created for one target.
- SOCKS proxies had their scheme stripped and were silently treated as HTTP.
- `Config` silently accepted typo'd keyword arguments; unknown options now warn.
- `chuscraper.__version__` was hardcoded and had drifted from the released version.
- Implemented the `production_ready` and `humanize` Config presets that the test
  suite described but which were never built.
- Added `Tab.mouse_drag()`, documented in the README but missing.
- `Tab.crawl()` never crawled and ignored `depth`; deprecated in favour of
  `Tab.map_links()` and `chuscraper.spider.Crawler`.

### Packaging & CI

- **`grapheme` is now an optional dependency.** Its 2020-era `setup.py` fails to
  build on modern setuptools, which could make `pip install chuscraper` fail
  outright. A built-in cluster splitter is used when it is absent; install
  `chuscraper[grapheme]` for full Unicode segmentation.
- `import chuscraper` no longer requires `playwright`, which was being imported
  eagerly just to compute a file path.
- Added a CI workflow that runs the test suite, lints for undefined names, and
  syntax-checks every JS bypass. The repo previously had no test CI at all.
- Added the missing `tests/conftest.py`; several test modules imported it and
  failed at collection, taking the whole suite down.
- `tests/core/test_stealth.py` imported a function that does not exist and had
  not run in a long time; rewritten against the real API.

### Behaviour changes to be aware of

- `MarkdownConverter.convert()` now raises `MarkdownConversionError` on failure
  instead of returning the error message as content.
- `MobileElement.click()` now raises `ValueError` on unparseable bounds instead
  of failing silently.
- `Tab.crawl()` is deprecated; use `Tab.map_links()` or `spider.Crawler`.
- `Tab.get_all_urls()` gained a `navigable=` parameter; the crawler uses it to
  skip assets and non-http schemes.
