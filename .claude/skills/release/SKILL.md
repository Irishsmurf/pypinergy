---
name: release
description: Cut a pypinergy release — bump the version in both files, run unit tests, tag, and push to trigger the PyPI publish workflow.
disable-model-invocation: true
---

Release pypinergy at version `$ARGUMENTS` (e.g. `/release 0.2.0`). If no version was given, read the current version from `pyproject.toml` and ask the user whether this is a patch, minor, or major bump.

1. Confirm the working tree is clean and on `main` (`git status`, `git branch --show-current`). Stop if either fails.
2. Update `version` in `pyproject.toml` and `__version__` in `src/pypinergy/__init__.py` to the new version. They must match — the publish workflow verifies the tag against `pyproject.toml`.
3. Run `pytest tests/unit/ -v`. Stop on any failure.
4. Commit both files: `chore: release v<version>`.
5. Tag `v<version>` and show the user the commit and tag, then ask for confirmation before pushing.
6. On confirmation: `git push origin main --follow-tags`. The `publish.yml` workflow builds the package, verifies the tag matches the version, publishes to PyPI, and creates the GitHub release.
7. Suggest watching the run with `gh run watch` and verifying the new version appears on PyPI.
