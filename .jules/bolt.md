## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-02-28 - Caching module-level references in parsing loops
**Learning:** Repeated lookups of module-level objects (like `datetime.fromtimestamp` and `timezone.utc`) inside tight parsing loops (e.g. converting arrays of timestamp strings) incur a measurable overhead. Benchmarks showed caching these references (`_from_ts = datetime.fromtimestamp`) alongside combining safe built-in conversions (`int()`) improves the happy path execution by ~25%, dropping execution time from ~1.48s to ~1.17s per million calls.
**Action:** In data-intensive parsing functions, alias frequently accessed library functions or constants at the module level. Rely on native C-extensions like `int()` for safe type conversion and whitespace stripping rather than custom string validation (`isdigit()`), which slows down the happy path.
