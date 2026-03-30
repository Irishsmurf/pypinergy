## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-02 - Bypassing type coercion for common fallbacks
**Learning:** In dataclass parsing pathways, fields that fallback to `0` or `"0"` repeatedly execute `try...except int(ts)` type coercion. Bypassing this with an explicit fast-path (`if ts == 0 or ts == "0"`) provides a measurable performance improvement (~6x faster for those values) by skipping the exception overhead and avoiding `_fromtimestamp` instantiation.
**Action:** When parsing variables, add fast-paths to bypass integer coercion/parsing for commonly occurring default or fallback values.
