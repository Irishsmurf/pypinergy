## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.

## 2024-05-06 - Memory Optimization for Heavy API Payloads
**Learning:** For Python 3.10+, using the `slots=True` parameter on heavily instantiated `@dataclass` API models significantly reduces memory footprint (from ~296 bytes to ~80 bytes per instance) and slightly improves instantiation speed by avoiding dynamic `__dict__` allocations. This is highly relevant for wrapping APIs that return large series of metrics.
**Action:** Always conditionally use `_DATACLASS_KWARGS = {'slots': True} if sys.version_info >= (3, 10) else {}` and apply it to `@dataclass` definitions that will be instantiated hundreds or thousands of times.

## 2024-05-27 - Eliminating mutable default allocation overhead
**Learning:** In Python, providing a mutable collection literal like `[]` or `{}` as the default argument to `dict.get()` (e.g., `d.get('key', [])`) allocates a new list or dictionary object every single time the expression is evaluated, even if the key is found. In high-throughput parsing loops (like API models processing large nested JSON responses), this causes measurable memory allocation and garbage collection overhead. Using the `or` operator (e.g., `d.get('key') or ()`) provides a nearly ~45% performance boost because Python doesn't allocate the fallback unless `d.get()` returns a falsy value. Using empty tuples `()` for iterables is even better, as an empty tuple is a CPython singleton.
**Action:** When extracting data from dictionaries on performance-critical paths, use `d.get('key') or {}` or `d.get('key') or ()` instead of passing `[]` or `{}` as the default argument to `get()`. Ensure correct parenthesis usage if chaining `.get()` calls (e.g., `(d.get("key") or {}).get("sub") or {}`).
