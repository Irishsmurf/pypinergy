## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-03 - Fast path for zero-value timestamps
**Learning:** Parsing a timestamp fallback value `0` (or `"0"`) via the standard `try...except int(ts)` path and instantiating a new aware datetime is slower than returning a pre-cached global constant `_EPOCH_UTC`. Given that APIs sometimes return `0` or `"0"` for empty periods or fallback defaults in usage entries, adding an explicit fast path skips exception handling and parsing overhead.
**Action:** Check if common fallback/default parameter values like `0` can bypass normal parsing logic and directly return pre-calculated module-level constants.
