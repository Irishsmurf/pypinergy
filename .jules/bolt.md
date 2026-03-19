## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-02 - HTTP Session Header Pre-Allocation
**Learning:** In an IO-bound HTTP client like PinergyClient, micro-optimizations like replacing f-strings with concatenation yield no real-world measurable impact. However, repeatedly passing the `auth_token` as a `headers` dictionary to `requests.Session.get()` incurs unnecessary dictionary instantiation and merging overhead on every request.
**Action:** Pre-allocate persistent headers directly onto the `requests.Session` object (via `session.headers.update()`) upon login, which simplifies internal API calls and marginally reduces Python overhead.
