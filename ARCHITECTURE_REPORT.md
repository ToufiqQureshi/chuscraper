# Architecture & Production Readiness Report

## 1. Executive Summary
The `chuscraper` library is a Python-based browser automation framework built directly on top of the Chrome DevTools Protocol (CDP). It distinguishes itself by avoiding Selenium/WebDriver in favor of direct WebSocket communication, allowing for stealthier operations and finer control.

**Current Status:** Functional prototype with strong core concepts but significant stability risks for production use. The architecture is monolithic in places and relies on hardcoded configurations that limit scalability and stealth adaptability.

**Key Recommendation:** Prioritize stability fixes (process management, connection handling) before expanding features. Decouple the stealth and configuration modules to support dynamic updates without code changes.

---

## 2. Architecture Overview

### High-Level Design
```mermaid
graph TD
    User[User Code] --> Browser[Browser Class]
    Browser --> |Manages| Process[Chrome Process]
    Browser --> |Connects via| Connection[Connection Class]
    Connection --> |WebSockets| CDP[Chrome DevTools Protocol]

    Browser --> |Contains| TargetManager[Target Manager]
    TargetManager --> |Tracks| TabList[List[Tab]]

    Tab[Tab Class] --> |Inherits| Connection
    Tab --> |Uses| Mixins[Navigation, DOM, Network, etc.]

    Stealth[Stealth Module] --> |Injects JS| Tab
    Config[Config Class] --> |Settings| Browser
```

### Core Modules & Responsibilities

| Module | Responsibility | Key Classes |
|--------|----------------|-------------|
| **`core.browser`** | Process lifecycle, global connection management, context handling. | `Browser`, `HTTPApi` |
| **`core.connection`** | WebSocket communication, event dispatching, transaction matching. | `Connection`, `Transaction` |
| **`core.tab`** | Represents a single page/target. Main API for user interaction. | `Tab` (composed of mixins) |
| **`core.stealth`** | Generates anti-detection JS payloads. | `get_stealth_scripts` |
| **`core.config`** | Configuration object for browser launch arguments. | `Config` |
| **`core.intercept`** | Network request interception and modification. | `BaseFetchInterception` |

### Data Flow
1.  **Input:** User initializes `Browser(config)` -> Spawns Chrome process.
2.  **Connection:** `Browser` establishes WebSocket connection to `browser` target.
3.  **Discovery:** `TargetManager` listens for `TargetCreated` events to instantiate `Tab` objects.
4.  **Processing:** User calls methods on `Tab` (e.g., `.goto()`, `.select()`).
5.  **Action:** `Tab` sends JSON-RPC commands via `Connection.send()`.
6.  **Extraction:** `Tab` retrieves DOM/Content -> helper methods (e.g., `markdown()`) process data.
7.  **Output:** Returns Python objects (Strings, Elements, Lists) to user.

---

## 3. Production Readiness Review

### Strengths
*   **Direct CDP Access:** Bypasses WebDriver, reducing detection surface.
*   **Mixin Architecture:** `Tab` and `Element` functionality is reasonably modularized.
*   **Stealth Foundation:** Implements advanced techniques (prototype patching, job objects on Windows).
*   **Lightweight:** Minimal dependencies compared to Playwright/Selenium.

### Major Weaknesses
*   **Hardcoded Stealth:** User Agents and Chrome versions are hardcoded in `stealth.py` and `fingerprint_profiles.py`. This is a "fingerprint farm" risk.
*   **Race Conditions:** Port discovery and target attachment have race windows that can cause crashes or hangs.
*   **Error Handling:** "Swallow and log" pattern is prevalent (e.g., `try...except Exception: pass`), hiding critical failures.
*   **Monolithic `Browser`:** The `Browser` class mixes process management, connection logic, and context management.

### Top 5 Crash Risks (P0 Fixes)

1.  **Port Discovery Race Condition**
    *   **File:** `chuscraper/core/browser.py`
    *   **Function:** `Browser.start`
    *   **Risk:** The code attempts to read `stderr` to find the DevTools port. If Chrome starts too fast or outputs differently, `found_port` remains `None`, leading to a connection failure. The timeout is fixed at 10s.
    *   **Fix:** Implement a retry loop that checks for the port file (UserDataDir/DevToolsActivePort) as a fallback, or use a pipe listener that doesn't block.

2.  **Target Attachment Hang**
    *   **File:** `chuscraper/core/browsers/target_manager.py`
    *   **Function:** `_handle_attached_to_target`
    *   **Risk:** If `stealth` injection fails or the target closes immediately (e.g., an ad iframe), the `run_if_waiting_for_debugger` command might not be sent. This leaves the tab in a "frozen" paused state forever.
    *   **Fix:** Wrap the stealth injection in a `try/finally` block that *guarantees* resumption of the target, regardless of errors.

3.  **WebSocket Reconnection Failure**
    *   **File:** `chuscraper/core/connection.py`
    *   **Function:** `Connection.send`
    *   **Risk:** If `self.closed` is true, it calls `await self.connect()`. However, if the browser process is dead, this will hang or raise an unhandled `ConnectionRefusedError`.
    *   **Fix:** Check process liveness before attempting to reconnect. Fail fast if the browser is gone.

4.  **Zombie Processes on Linux/Mac**
    *   **File:** `chuscraper/core/browser.py`
    *   **Function:** `Browser.stop`
    *   **Risk:** The rigorous `JobObject` cleanup is Windows-only. On Linux/Mac, `self._process.kill()` leaves child processes (renderers, GPU process) orphaned if the parent Python script crashes hard.
    *   **Fix:** Implement a process group kill (`os.killpg`) or use a signal handler to ensure the entire tree is reaped.

5.  **Unhandled Event Parsing**
    *   **File:** `chuscraper/core/connection.py`
    *   **Function:** `_handle_message`
    *   **Risk:** The heuristic event mapping (`domain_name.lower()`) is fragile. If CDP introduces a new event or changes casing, `event_type` will be `None`, and handlers won't fire. This breaks logic relying on specific events (like `RequestPaused`).
    *   **Fix:** Use a robust, generated mapping of Method Name -> Class, or allow string-based fallback handlers.

---

## 4. Actionable Recommendations & Roadmap

### Phase 1: Stability First (P0 - Immediate)
*   **[P0] Fix Port Discovery:** Rewrite `Browser.start` to reliably detect the port using both `stderr` parsing and the `DevToolsActivePort` file check.
*   **[P0] Robust Target Resumption:** Ensure `Runtime.runIfWaitingForDebugger` is *always* called in `target_manager.py`, wrapping stealth injection in a `suppress(Exception)` block.
*   **[P0] Connection Guard Rails:** Update `Connection.send` to throw explicit `BrowserCrashedError` if the backend is gone, rather than hanging.
*   **[P0] Process Cleanup:** Implement `atexit` handlers and signal handlers to reliably kill the browser process tree on non-Windows platforms.

### Phase 2: Dynamic Stealth (P1 - High Priority)
*   **[P1] Externalize Profiles:** Move `PROFILES` from `fingerprint_profiles.py` to a JSON/YAML configuration file.
*   **[P1] Dynamic User Agent:** Update `Config` to accept a `profile_path` or `profile_dict` instead of just a raw User Agent string.
*   **[P1] Version Decoupling:** Remove hardcoded "124.0.x" strings from `stealth.py`. Allow these to be passed via the profile configuration.

### Phase 3: AI Readiness & Scalability (P2 - Medium Priority)
*   **[P2] Extraction Interface:** Define an `Extractor` abstract base class. Refactor `markdown()` to use this interface. This allows users to plug in `LLMExtractor` or `JsonExtractor` later.
*   **[P2] Event Bus:** Replace the ad-hoc `handlers` list in `Connection` with a proper `EventEmitter` pattern for better debuggability.
*   **[P2] Error Recovery:** Implement a "Health Check" task in `Browser` that periodically pings the browser and auto-restarts if it becomes unresponsive (Self-Healing).

---

## 5. Quick Wins (Low Effort, High Impact)
1.  **Logging:** In `core/browser.py`, change `logging.basicConfig` to use a standard format that includes timestamps (already partly there, but inconsistent).
2.  **Timeouts:** Add a default `timeout=30` to `Connection.send` to prevent infinite hangs on dead sockets.
3.  **Typos:** Fix `medimize` -> `normalize` in `core/tab.py`.
