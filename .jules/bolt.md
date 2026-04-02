## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.
## 2025-03-02 - Dictionary Parsing in Dataclass Methods
**Learning:** Redundant type conversions on fallback dictionary values (e.g., `float(d.get("key", 0.0))` or `bool(d.get("key", False))`) incur unnecessary overhead, slowing down list comprehension parsing by ~20%. Using assignment expressions `float(v) if (v := d.get("key")) is not None else 0.0` or raw getters like `d.get("key", False)` is measurably faster, especially when fields are missing or valid.
**Action:** When extracting dictionary fields in hot parsing loops, avoid redundant function calls to `bool()`, `float()`, or `int()` if the type is inherently stable or missing, using `:=` to extract and type-cast in one efficient step.

## 2025-03-02 - Avoiding theoretical default values in hot paths
**Learning:** Adding fallback defaults like `0` to dictionary lookups (e.g., `d.get("date", 0)`) when passing the value to a parsing helper (`_parse_ts_pair`) bypasses the helper's internal fast-path for missing/`None` values. Evaluating `0` triggers `int(0)` coercion and `datetime.fromtimestamp(0)` instantiation, which is ~9x slower than returning `None` immediately, causing a measurable bottleneck in list comprehension parsing for missing fields.
**Action:** Let naturally missing dictionary values return `None` so dedicated parsing helpers can leverage their early-exit fast-paths, rather than forcing a theoretical default that forces full processing.
