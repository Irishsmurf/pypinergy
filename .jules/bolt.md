## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-02 - Caching requests auth_token in session.headers
**Learning:** The `requests` library incurs a measurable overhead (~40-50% speedup per request instantiation) when passing dynamic `headers=` keyword arguments on every request, because it repeatedly instantiates, merges, and validates header dictionaries internally.
**Action:** Pre-allocate persistent headers (like `auth_token`) directly in `session.headers.update()` instead of passing them to `session.get()` or `session.post()`. Use a property setter (e.g., `_auth_token.setter`) to automatically keep the session headers in sync with the current token state without risking regressions.
