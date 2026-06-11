# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Full project guide (layout, conventions, common tasks): @AGENTS.md

## Rules that override or extend AGENTS.md

- **Tests:** run only `pytest tests/unit/ -v` by default. Do not run `tests/integration/` — those hit the real Pinergy API, and the full tier reads real credentials from `.env`. They are run manually by the maintainer.
- **`.env` contains real account credentials.** Never print, commit, or copy its contents.
- **Version bumps:** update `version` in `pyproject.toml` AND `__version__` in `src/pypinergy/__init__.py` — they must match (`test_version_matches_pyproject` enforces this).
- **Commits:** use conventional-commit prefixes (`feat:`, `fix:`, `perf:`, `chore:`, `docs:`, `test:`).
- **README:** any change to the public API or workflows must update README.md in the same piece of work (examples, field tables, exception table, release instructions).
- **Security invariants** (see `.jules/sentinel.md` for history) — do not regress:
  - Base URL must be HTTPS (localhost excepted).
  - The session disables redirects (`_NoRedirectSession`) to prevent auth-header leakage.
  - `logout()` must clear both the token and the stored password hash.
- Performance patterns used in this codebase (cached `_EPOCH_UTC`, EAFP coercion, `slots=True` dataclasses) are documented in `.jules/bolt.md` — keep new code consistent with them.
