# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Prevent CRLF HTTP Header Injection in check_email (#188).

## [1.0.0] - 2026-06-13

### Added
- `LevelPayDailyValue.day_kwh` is now typed as `Dict[str, float]` (tariff band name → kWh) rather than `Dict[str, Any]`.
- Expanded API reference documentation to cover all 26 exported symbols.
- Python 3.13 added to CI test matrix.
- Troubleshooting section in the user guide.

### Changed
- PyPI classifier upgraded from `4 - Beta` to `5 - Production/Stable`. The public API is stable.

## [0.1.9] - 2026-06-12

### Changed
- README logo URLs made absolute for correct rendering on PyPI.

## [0.1.8] - 2026-06-12

### Changed
- Added PyPinergy branding, logos, and custom MkDocs theme styling.
- Enabled Mermaid diagram support in MkDocs.
- Added lazy auth flow diagram and contributing guide to documentation.

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
