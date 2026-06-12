## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.

## 2024-05-06 - Memory Optimization for Heavy API Payloads
**Learning:** For Python 3.10+, using the `slots=True` parameter on heavily instantiated `@dataclass` API models significantly reduces memory footprint (from ~296 bytes to ~80 bytes per instance) and slightly improves instantiation speed by avoiding dynamic `__dict__` allocations. This is highly relevant for wrapping APIs that return large series of metrics.
**Action:** Always conditionally use `_DATACLASS_KWARGS = {'slots': True} if sys.version_info >= (3, 10) else {}` and apply it to `@dataclass` definitions that will be instantiated hundreds or thousands of times.

## 2025-03-02 - Replacing _as_list with (d.get(key) or [])
**Learning:** Using a custom `_as_list` function to safely parse lists from dictionary defaults adds unnecessary function call overhead on the happy path. Using the pattern `(d.get(key) or [])` or `(d.get(key) or ())` (for comprehensions) achieves the same safe parsing with ~2x performance.
**Action:** Replace `_as_list(d.get("key"))` with `(d.get("key") or [])` or `(d.get("key") or ())` directly in list comprehension loops and assignments, and avoid defining generic conversion helper functions for lists if we can use the `or` fallback instead.
