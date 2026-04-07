## 2025-02-28 - Reusing datetime constant for faster parsing
**Learning:** Instantiating a new timezone-aware `datetime` inside a dataclass fallback method (like `_from_dict`) creates a measurable performance bottleneck when parsing arrays of objects. A `timeit` test showed instantiation takes ~0.84s per million calls, versus ~0.02s when reusing a constant.
**Action:** Always check for module-level constants (e.g., `_EPOCH_UTC`) before creating new aware datetime objects in tight loops or parsing logic.

## 2025-03-01 - Optimizing type coercion and module lookups
**Learning:** Using `isinstance(val, type)` followed by parsing is often slower than EAFP (`try...except int(val)`) on the happy path. Additionally, accessing module-level attributes like `datetime.fromtimestamp` and `timezone.utc` inside hot parsing functions creates a bottleneck; caching these as module-level constants speeds up tight loops by avoiding repeated lookups.
**Action:** Use `try...except` blocks directly instead of type checking before coercing in performance-critical paths, and cache frequently used functions/constants from imported modules at the module scope.

## 2025-03-01 - Dataclass slots=True vs __slots__
**Learning:** In Python 3.10+, adding `slots=True` to the `@dataclass` decorator is the standard way to create slotted dataclasses. Attempting to manually define `__slots__ = ("field1", "field2")` inside a dataclass that has fields defined will raise `ValueError: 'field_name' in __slots__ conflicts with class variable`.
**Action:** Always use `@dataclass(slots=True)` for dataclass slot optimization instead of defining `__slots__` explicitly inside the class body, and apply it comprehensively across all relevant models for consistency.
## 2025-03-01 - Dataclass slots=True vs __slots__ in Python <3.10
**Learning:** `slots=True` in the `@dataclass` decorator is only supported in Python 3.10+. If the library supports older versions (e.g., Python 3.9), we must manually define `__slots__ = ("field1", "field2")` inside the class. However, we cannot do this for dataclasses that rely on `dataclasses.field()` assignments (like `field(repr=False)`), as it will raise a `ValueError: 'field_name' in __slots__ conflicts with class variable` when `dataclass` parses the class.
**Action:** When optimizing dataclass memory in projects that support Python <3.10, limit explicit `__slots__` definitions to classes that do not use `field(...)` default assignments, and never use `@dataclass(slots=True)`.
