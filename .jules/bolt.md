## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-02 - Avoid mutable defaults in dict.get() for high-throughput loops
**Learning:** In Python, providing a mutable collection literal like `d.get('key', [])` allocates a new list object every time the expression is evaluated, creating measurable overhead (~40-60% slower) in high-throughput parsing loops even when the key exists.
**Action:** When extracting lists inside dataclass parsing loops (`_from_dict`), use `d.get(key) or []` for direct assignments and `(d.get(key) or ())` in list comprehensions to avoid unnecessary list allocation on the happy path.

## 2025-03-02 - Avoid mutable defaults in dict.get() for dictionaries
**Learning:** Just like with lists, providing a mutable literal like `{}` as a default in `d.get("key", {})` allocates a new empty dictionary object on every evaluation, causing measurable overhead in hot parsing functions.
**Action:** Replace `d.get(key, {})` with `d.get(key) or {}` to avoid the allocation when the key is present.
