## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-05-15 - Immutable Defaults and __slots__ for High-Frequency Dataclasses
**Learning:** Using `d.get("key", [])` or `d.get("key", {})` allocates a new empty list or dict every time the fallback is hit, penalizing the happy path in high-throughput parsing loops. Replacing these with `d.get("key") or []` (or `()` for iterations) eliminates this overhead. Additionally, applying `slots=True` to heavily instantiated dataclasses like `UsageEntry` significantly reduces memory overhead and improves instantiation speed on Python 3.10+.
**Action:** Always use truthiness fallbacks like `d.get("key") or []` instead of mutable literal arguments to `dict.get()`, and apply conditional `slots=True` to dataclasses that parse bulk API data (like arrays of entries).
