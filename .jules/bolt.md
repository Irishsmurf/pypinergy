## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-01 - Avoid unnecessary mutable default allocations in dict.get()
**Learning:** Providing a mutable collection literal like `d.get('key', [])` or `{}` allocates a new object every time the expression is evaluated, even if the key exists. In high-throughput parsing loops, this introduces measurable overhead. Using `d.get(key) or []` (or `()` for tuples) avoids allocation on the happy path. Empty tuples `()` are particularly optimal as they are CPython singletons.
**Action:** When extracting lists or dicts from JSON responses in hot loops, use `(d.get(key) or ())` for comprehensions and `d.get(key) or []` or `d.get(key) or {}` for assignments to prevent unnecessary memory allocations.
