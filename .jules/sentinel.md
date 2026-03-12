## 2025-05-14 - JavaScript Injection via CSS Selectors
**Vulnerability:** JavaScript Injection in `DomMixin` methods (`query_selector`, `query_selector_all`) when falling back to runtime evaluation.
**Learning:** Using Python f-strings or string formatting to inject variables into JavaScript template literals (backticks) is dangerous if the variables are user-controlled.
**Prevention:** Always use `json.dumps()` to escape Python strings before injecting them into JavaScript code to ensure they are treated as safe string literals.
