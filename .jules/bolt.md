## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-02 - [Models] Fast path for default/null values in frequently called dataclass parsers
**Learning:** High-volume string/integer parsing for repeated default values (like timestamp "0" or 0) in heavily used dataclass mapping logic incurs significant overhead due to generic validation logic (`try...except`, `.isdigit()`) or complex class instantiations (`datetime.fromtimestamp`).
**Action:** Always implement a dedicated fast path (`if val in (0, "0"): return cached_result`) for commonly occurring fallback values at the very top of parsing functions to bypass unneeded computation and `try...except` block overhead.
