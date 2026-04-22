## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-04-22 - Reducing memory footprint of heavily instantiated dataclasses
**Learning:** For Python 3.9+ dataclasses that are instantiated frequently (e.g. elements of arrays in API responses like `UsageEntry` or `LevelPayDailyValue`), the default `__dict__` behavior causes significant memory overhead. Manually defining `__slots__` (e.g. `__slots__ = ("field1", "field2")`) reduces the memory footprint of each instance by up to ~75% and slightly speeds up instantiation. However, it cannot be used if fields require custom attribute behavior like `field(repr=False)`.
**Action:** Add `__slots__` explicitly to hot-path dataclasses that represent arrays of homogeneous data.
