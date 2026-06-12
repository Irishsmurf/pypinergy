# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.7] - 2026-06-11

### Fixed
- Raise `PinergyAuthError` for token rejection reported as `success:false` with HTTP 200. Stale tokens are now dropped automatically.

## [0.1.6] - 2026-06-11

### Added
- Context manager support for `PinergyClient`.
- `PinergyTimeoutError` and `PinergyResponseError` exceptions.
- `*_dt` alias fields in models for better naming consistency.
- Automatic token self-healing on 401 errors.

### Changed
- Improved model parsing robustness.
- Hardened client lifecycle management.

## [0.1.0] - 2026-06-01

### Added
- Initial release with support for usage, balance, top-ups, and comparison.
