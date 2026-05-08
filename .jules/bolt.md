## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-02 - Avoiding mutable default argument overhead in dict.get()
**Learning:** Using `d.get("key", [])` or `d.get("key", {})` allocates a new list or dict object every time the expression is evaluated, penalizing performance in high-throughput parsing loops. Using `d.get("key") or []` and `d.get("key") or {}` entirely avoids this allocation on the happy path. For list comprehensions, `(d.get("key") or ())` avoids allocations when falling back and safely handles when explicit `None` is in the dict.
**Action:** Always use `or []` or `or {}` instead of providing mutable literal defaults to `.get()` when evaluating in hot paths.
