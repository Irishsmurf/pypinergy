## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-05 - Avoid list instantiation overhead in dictionary fallbacks
**Learning:** In Python, providing a constant literal default argument to dict.get() for strings or integers (e.g., `d.get('key', 0)`) has virtually zero overhead, but mutable collection literals like `d.get('key', [])` or `{}` allocate a new object every time the expression is evaluated. In high-throughput loops or model instantiation during parsing, this list allocation adds up.
**Action:** In high-throughput parsing logic, replace mutable fallbacks with empty tuples for loops `for x in (d.get(key) or ())` to completely avoid memory allocation on the happy path, since `()` is a CPython singleton. For direct assignment use `d.get(key) or []`.
