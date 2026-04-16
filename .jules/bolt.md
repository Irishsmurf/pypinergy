## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-04-16 - Add __slots__ to heavily instantiated dataclasses
**Learning:** For Python 3.9+ dataclasses that are heavily instantiated (like array items in time-series API responses), manually defining `__slots__` significantly reduces memory overhead (~75% reduction by removing the `__dict__` overhead per instance) and slightly improves instantiation speed.
**Action:** Identify dataclasses that represent elements of large lists (e.g., `UsageEntry`, `LevelPayDailyValue`) and define `__slots__ = ("field1", "field2", ...)` on them to optimize memory usage and performance in high-throughput parsing loops. Note: Avoid adding manual slots to dataclasses with fields defined using `field(repr=False)` as they conflict with manual slots in older Python versions unless handled carefully.
