## 2025-05-14 - Prevent JS Injection in CDP Evaluation
**Vulnerability:** User-provided CSS selectors were interpolated directly into JavaScript backticks (template literals) using f-strings for `cdp.runtime.evaluate`.
**Learning:** Malicious selectors containing backticks could break out of the JavaScript string context, allowing arbitrary code execution within the browser's page context.
**Prevention:** Always use `json.dumps()` in Python to safely escape and quote strings before embedding them into JavaScript code snippets. This ensures the data is treated as a literal string in JS.
