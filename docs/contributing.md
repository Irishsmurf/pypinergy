# Contributing to PyPinergy

Thank you for your interest in contributing to **PyPinergy**!

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/irishsmurf/pypinergy.git
   cd pypinergy
   ```

2. **Install in editable mode with dev dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

## Coding Standards

- **Type Hints:** All public methods and functions must have type hints.
- **Linting:** We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting. Run it with:
  ```bash
  ruff check .
  ruff format .
  ```
- **Static Analysis:** Use `mypy` to verify types:
  ```bash
  mypy src/pypinergy
  ```

## Testing

We use `pytest` for all tests.

### Unit Tests
Unit tests use the `responses` library to mock API calls. They do not require an internet connection or Pinergy credentials.
```bash
pytest tests/unit/
```

### Integration Tests
Integration tests hit the real Pinergy API.

- **Network-only (no credentials):**
  ```bash
  pytest tests/integration/ -m network
  ```
- **Full (requires credentials):**
  ```bash
  export PINERGY_EMAIL="your-email"
  export PINERGY_PASSWORD="your-password"
  pytest tests/integration/
  ```

## Adding a New Endpoint

1. **Model:** Add a new dataclass to `src/pypinergy/models.py` with a `_from_dict` method.
2. **Client:** Add the corresponding method to `PinergyClient` in `src/pypinergy/client.py`.
3. **Export:** Export the new model in `src/pypinergy/__init__.py`.
4. **Test:** Add a unit test in `tests/unit/test_client.py` using a mock response.

## Pull Request Process

1. Create a branch for your feature or bugfix.
2. Ensure all tests pass and linting is clean.
3. Update the `CHANGELOG.md` with your changes.
4. Submit the PR against the `main` branch.
