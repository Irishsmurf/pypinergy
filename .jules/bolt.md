## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.

## 2025-03-02 - Enabling slots on dataclasses
**Learning:** For Python 3.10+, defining `__slots__` via the `slots=True` parameter on dataclasses significantly reduces deep memory footprint (from ~344 bytes to ~80 bytes) and slightly improves instantiation time, which is critical for parsing arrays of heavily instantiated models like time-series API responses. Additionally, dynamically setting `_DATACLASS_KWARGS = {'slots': True} if sys.version_info >= (3, 10) else {}` allows safe application across models in packages supporting Python 3.9+.
**Action:** Always enable `slots=True` on dataclasses representing data models, especially those dynamically parsed from lists or APIs.

## 2025-03-02 - Dictionary fallback micro-allocation overhead
**Learning:** In Python, passing mutable collection literals (like `[]` or `{}`) as the default argument in `dict.get('key', [])` allocates a new object every time the expression is evaluated. In high-throughput parsing loops (such as mapping array items), this repeated allocation introduces noticeable overhead. Refactoring to use logical OR, such as `d.get('key') or []` or `d.get('key') or ()`, bypasses this allocation on the happy path. Using `()` is particularly optimal when iterating since an empty tuple is a CPython singleton.
**Action:** Avoid mutable collection literals in `dict.get()` default arguments in tight loops; use logical OR fallbacks like `or {}` or `or ()` to prevent unnecessary allocations.
