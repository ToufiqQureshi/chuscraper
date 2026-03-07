## 2025-05-15 - [CSS Selector Injection Prevention]
**Vulnerability:** JavaScript injection through unsanitized CSS selectors in CDP evaluation templates.
**Learning:** Using Python f-string interpolation with backticks (`` ` ``) for JavaScript template literals allows attackers to break out of the string context and execute arbitrary JS if the input contains backticks or `${}`.
**Prevention:** Always use `json.dumps()` to escape Python strings being passed into JavaScript execution contexts via CDP. This ensures the input is properly quoted and escaped for the JS engine. Additionally, cast numeric values (like array indices) to `int()` to prevent index-based injection.
