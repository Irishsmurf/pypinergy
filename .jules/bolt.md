## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-02 - Memory overhead and dataclass slots
**Learning:** For Python 3.10+, defining dataclasses without `slots=True` significantly increases memory footprint due to the hidden `__dict__` overhead. A script showed `UsageEntry` size dropped from ~344 bytes to ~80 bytes (a ~76% reduction) and instantiation time dropped from ~0.43s to ~0.40s (1 million calls) when using slots.
**Action:** When working with Python 3.10+ dataclasses, apply the conditional `@dataclass(**{"slots": True} if sys.version_info >= (3, 10) else {})` to reduce object footprint, especially for objects created in bulk.

## 2025-03-02 - Avoid re-evaluating list comprehensions with `d.get(key) or []`
**Learning:** Using `d.get(key) or []` is slightly faster than `d.get(key, [])` when a key might exist but have an explicit `None` value (which would crash `d.get(key, [])` if iterated over).
**Action:** Use `(d.get(key) or [])` over `d.get(key, [])` to protect against explicit nulls and marginally improve happy-path execution speed in parsing.
