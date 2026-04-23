## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-02 - Avoid list allocation in dictionary get fallbacks
**Learning:** In Python, providing a mutable collection literal like `d.get('key', [])` allocates a new list object every time the expression is evaluated. While a literal scalar fallback like `0` has no overhead, allocating `[]` on missing keys hurts performance in tight loops or large arrays.
**Action:** Use `d.get(key) or []` in assignments and `(d.get(key) or ())` in comprehensions/iterations to avoid allocating unnecessary collections on the happy path.
