## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-24 - Bypassing type casting and instantiation on default timestamps
**Learning:** Default or missing timestamp values (e.g., `0` or `"0"`) frequently pass through parsing loops (like `_parse_ts_pair`) unchanged. Previously, they underwent `try...except int(ts)` type casting and subsequent aware datetime instantiation. Fast-pathing these common inputs to directly return the module-level `_EPOCH_UTC` constant avoids this overhead completely.
**Action:** When parsing dataclass fields or variables, explicitly define fast-paths (`if val == 0` or `val == "0"`) for commonly occurring default or fallback values to bypass parsing overhead and directly return cached constants.
