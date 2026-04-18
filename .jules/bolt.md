## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-05 - __slots__ for Data Class Instances in Time-Series
**Learning:** For Python 3.9+ dataclasses that are heavily instantiated (e.g., arrays of items like `UsageEntry` and `LevelPayDailyValue` in time-series responses), manually defining `__slots__` reduces memory overhead by ~75% per instance (from ~344 bytes to ~80 bytes) and gives a minor (~8%) instantiation speed boost. However, assigning `__slots__` conflicts with `field(repr=False)` in Python 3.9 because `field()` descriptors cause a class variable conflict.
**Action:** Add `__slots__` to high-volume time-series dataclasses (like `UsageEntry` and `LevelPayDailyValue`) to significantly reduce memory allocation during large parsing loops, while explicitly avoiding classes with `field()` attributes to prevent crashes.
