## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-27 - Fast-path parsing for default fallback values
**Learning:** Default API values (like `0` or `"0"` for timestamps) cause a significant parsing bottleneck when evaluated through standard coercion loops `try...except int(val)` and `fromtimestamp`. Benchmarking shows adding an explicit fast-path bypassing these steps creates a 5x-6x speed improvement on the happy-path fallback.
**Action:** When parsing dataclass fields or variables, explicitly define fast-paths (`if val == 0` or `val == "0"`) for commonly occurring default or fallback values to bypass parsing overhead and directly return cached constants.
