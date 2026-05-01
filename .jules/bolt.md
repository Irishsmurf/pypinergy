## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-02 - Memory overhead of Python dataclasses
**Learning:** Heavily instantiated `@dataclass` models in time-series API responses (like `UsageResponse` returning hundreds of `UsageEntry` objects) incur significant memory overhead (~39% more memory usage) in Python 3.9 because they use dynamic `__dict__` instances by default.
**Action:** Always manually define `__slots__` (e.g., `__slots__ = ("field1", "field2")`) for `@dataclass` classes that will be heavily instantiated in lists or arrays to dramatically reduce memory footprint. Avoid defining `__slots__` on classes with `field(repr=False)` to prevent class-level descriptor conflicts.
