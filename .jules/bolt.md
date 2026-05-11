## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-05-11 - Optimizing chained get calls
**Learning:** Using `(d.get(key) or ())` instead of `d.get(key, [])` in list comprehensions and assignments prevents unnecessary allocations of new empty list/dict objects when keys are missing or when truthy values with missing explicit keys evaluates to defaults in high-throughput loops. By avoiding these mutable collection literals, performance improves while retaining safe fallbacks for edge-case explicit `None` values that crash simple iterated defaults.
**Action:** Use `(d.get(key) or ())` and `(d.get(key) or {})` where empty defaults are needed in high-frequency parsing tasks or comprehensions.
