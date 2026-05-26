## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.

## 2024-05-06 - Memory Optimization for Heavy API Payloads
**Learning:** For Python 3.10+, using the `slots=True` parameter on heavily instantiated `@dataclass` API models significantly reduces memory footprint (from ~296 bytes to ~80 bytes per instance) and slightly improves instantiation speed by avoiding dynamic `__dict__` allocations. This is highly relevant for wrapping APIs that return large series of metrics.
**Action:** Always conditionally use `_DATACLASS_KWARGS = {'slots': True} if sys.version_info >= (3, 10) else {}` and apply it to `@dataclass` definitions that will be instantiated hundreds or thousands of times.


## 2024-05-26 - Reduce memory overhead via optimal `.get()` defaults
**Learning:** Providing mutable collection literals like `d.get('key', [])` or `{}` as the default argument allocates a new object every time the expression is evaluated.
**Action:** In high-throughput loops, use `d.get(key) or []` or `d.get(key) or {}` to avoid this allocation on the happy path. When possible inside list comprehensions, use `d.get(key) or ()` to take advantage of the empty tuple being a CPython singleton.
