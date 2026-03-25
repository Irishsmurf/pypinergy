## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2023-11-20 - Fast-paths for heavily used default timestamp values
**Learning:** During profiling, the `_parse_ts_pair` string/int coercion fallback was extremely heavily loaded due to the constant presence of "0" and 0 edge case fallback timestamps in models across arrays. Passing these through `try..except int()` and `fromtimestamp()` takes ~1-1.5 seconds per million iterations.
**Action:** Always explicitly define fast-paths (`if val == 0 or val == "0"`) returning constants (`0, _EPOCH_UTC`) for commonly occurring default or fallback integer/string values to bypass parsing overhead. This brings parsing time down to <0.15s per million operations for those values (~85%+ faster).
