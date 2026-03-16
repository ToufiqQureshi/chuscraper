## 2026-02-18 - [MEDIUM] JavaScript Injection in DOM Selectors
**Vulnerability:** Unsanitized string interpolation of CSS selectors into JavaScript templates passed to `CDP.runtime.evaluate`. An attacker could use a malicious selector like `` `); alert(1); // `` to execute arbitrary JavaScript in the browser context.
**Learning:** Even internal helper methods like `query_selector` that bridge the gap between Python and Browser JS can be vectors for injection if they use templates with backticks or unescaped quotes.
**Prevention:** Always use `json.dumps()` to serialize Python strings into JavaScript string literals when generating code for execution via CDP.
