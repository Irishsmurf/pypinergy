## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-02 - Memory overhead reduction via `__slots__`
**Learning:** For Python 3.9 dataclasses that are heavily instantiated in arrays (like time-series API responses), manually defining `__slots__` significantly reduces memory overhead (~50% reduction in object size) and slightly improves instantiation speed. However, defining `__slots__` on dataclasses that use `field()` (e.g., `field(repr=False)`) creates a class-level descriptor conflict in Python 3.9, resulting in a `ValueError`.
**Action:** Always verify if a dataclass uses `field()` before applying the `__slots__` optimization.
