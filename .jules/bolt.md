## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-05-03 - Optimizing dataclass memory overhead
**Learning:** Using `@dataclass` without `__slots__` creates a `__dict__` for every instance. For time-series API responses (like `UsageEntry` and `LevelPayDailyValue`) that instantiate thousands of objects in arrays, this creates significant memory overhead (~344 bytes vs ~80 bytes per object). Adding `__slots__` reduces memory usage by ~76% and slightly improves instantiation speed, but care must be taken to ensure no class-level descriptors (like `field(repr=False)`) conflict in older Python versions.
**Action:** Always add `__slots__` to dataclass models that represent heavily-instantiated items in arrays (e.g., historical time-series data) to optimize memory and GC pressure.
