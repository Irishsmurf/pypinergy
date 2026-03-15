# AGENTS.md

This file provides guidance for AI agents (Claude, Codex, etc.) working in this repository.

## Project Overview

**pypinergy** is an unofficial Python client library for the [Pinergy](https://pinergy.ie) smart-meter API — an Irish electricity provider. It reverse-engineers the mobile app's HTTP API to expose account data, usage statistics, balance queries, and top-up management as a clean Python interface.

- **PyPI:** `pypinergy`
- **Python:** 3.9+
- **License:** MIT
- **Status:** Beta

## Repository Layout

```
src/pypinergy/        # Package source
  __init__.py         # Public re-exports
  client.py           # PinergyClient — all API methods
  models.py           # Dataclass response models (_from_dict() parsers)
  exceptions.py       # PinergyError hierarchy
  _auth.py            # SHA-1 password hashing (internal)
tests/
  conftest.py         # Shared fixtures and mock payloads
  unit/               # Fully mocked tests (no network, no credentials)
  integration/        # Real-API tests (two tiers — see Testing section)
examples/             # Runnable usage scripts
.github/workflows/
  ci.yml              # Test matrix + Codecov upload
  publish.yml         # Build + PyPI + GitHub release on version tag
```

## Development Setup

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode along with `pytest`, `pytest-cov`, and `responses` (HTTP mocking).

## Testing

### Unit tests (no credentials, no network)

```bash
pytest tests/unit/ -v
```

These use the `responses` library to mock every HTTP call. They should always pass locally.

### Integration tests — network tier (no credentials needed)

```bash
pytest tests/integration/ -m network -v
```

These hit the real API with intentionally bad credentials to verify the live endpoint shape.

### Integration tests — full (requires real credentials)

```bash
export PINERGY_EMAIL=you@example.com
export PINERGY_PASSWORD=your-password
pytest tests/integration/ -v
```

In CI these run only on pushes to `main` (not on PRs from forks) to protect secrets.

### Coverage

```bash
pytest --cov=pypinergy --cov-report=html
```

## Code Conventions

- **Type hints** on all public functions/methods.
- **Dataclasses** for every API response model; each has a `_from_dict(data: dict)` classmethod.
- Unix timestamps are exposed as both a raw `int` field and a `datetime` field (UTC). The `datetime` field is named with a `_dt` suffix (e.g., `created_at_dt`).
- Raise the most specific exception in the `PinergyError` hierarchy:
  - `PinergyAuthError` — session / auth failures
  - `PinergyAPIError` — API returned an application-level error (includes `.error_code`)
  - `PinergyHTTPError` — network-level failure
- The `_auth.py` module is private (prefixed `_`). Don't call it outside `client.py`.
- The mobile app's `User-Agent` header (`okhttp/5.1.0`) must be preserved — the API rejects other agents.

## Key Design Decisions

- **Lazy vs. explicit auth:** `PinergyClient` can be instantiated with a token (already authenticated) or with email/password (login on first call). Both patterns are tested.
- **No dependencies beyond `requests`:** keep the runtime dependency surface minimal.
- **No async client:** the current implementation is synchronous. Don't add `asyncio` without discussion.

## Common Tasks

### Adding a new API endpoint

1. Add a method to `PinergyClient` in [src/pypinergy/client.py](src/pypinergy/client.py).
2. Add a response model (dataclass + `_from_dict`) to [src/pypinergy/models.py](src/pypinergy/models.py).
3. Export the new model from [src/pypinergy/__init__.py](src/pypinergy/__init__.py).
4. Add a mock payload to `tests/conftest.py` and cover it in `tests/unit/test_client.py`.

### Bumping the version

Update `version` in [pyproject.toml](pyproject.toml) only. The publish workflow reads from there; `__init__.py` does not need a separate version string.

### Publishing a release

Push a tag matching `v*` (e.g., `v0.2.0`). The `publish.yml` workflow builds the wheel, verifies the tag matches the package version, and uploads to PyPI via OIDC trusted publishing.

## CI/CD Notes

- `ci.yml` runs on every push and pull request, testing against Python 3.9–3.12.
- Coverage is uploaded to Codecov on the Python 3.12 run only (avoids duplicate reports).
- `publish.yml` requires the `PYPI_API_TOKEN` secret (or OIDC environment configured in the repo settings).
- Full integration tests in CI need `PINERGY_EMAIL` and `PINERGY_PASSWORD` repository secrets.

## Things to Avoid

- Don't mock the database or HTTP layer in integration tests — use the `responses` library only in `tests/unit/`.
- Don't import `_auth` outside of `client.py`.
- Don't add optional dependencies or extras beyond `[dev]` without a clear use-case.
- Don't break the `_from_dict` contract on existing models — downstream users may rely on field names.
