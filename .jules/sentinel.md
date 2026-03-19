
## 2024-03-17 - [Authorization Bypass via Incomplete Logout]
**Vulnerability:** The `logout()` method only cleared `self._auth_token` but left `self._password_hash` intact. Because `PinergyClient` implements automatic lazy-login, an explicit `logout()` followed immediately by an authenticated API request would silently log the user back in using the cached password hash.
**Learning:** When implementing lazy-login or automatic re-authentication features, an explicit `logout` action must comprehensively destroy all state that enables the automatic flow. If credentials (even hashes) are cached for convenience, they must be purged upon explicit logout.
**Prevention:** Always trace the full lifecycle of authentication state. If `login()` relies on multiple state variables (token AND password hash), `logout()` must clear them all. Write explicit unit tests that verify consecutive `logout() -> API call` sequences throw `AuthError` instead of succeeding.

## 2024-03-18 - [Header Leakage via Cross-Origin Redirects in requests]
**Vulnerability:** The Pinergy API client uses custom HTTP headers for authentication (`auth_token`, `email_address`). The `requests` library automatically follows redirects by default, but it only strips standard authentication headers (like `Authorization`) on cross-origin redirects. Non-standard headers like `auth_token` and `email_address` are sent to the new origin, potentially leaking credentials to an attacker if the API ever redirects to a malicious site.
**Learning:** `requests` will leak custom authentication headers across domain boundaries. Standard libraries often don't provide the same security guarantees for custom implementations as they do for standard ones (e.g. `Authorization`).
**Prevention:** When using custom headers for authentication, always explicitly disable automatic redirects (`allow_redirects=False`) or implement custom redirect handling that explicitly strips sensitive headers before following cross-origin redirects.

## 2025-03-19 - [Credential Leakage via Plaintext HTTP Transmission]
**Vulnerability:** The `PinergyClient` constructor allowed any arbitrary `base_url`, including `http://` URLs pointing to remote domains. Because the client sends the `email` and `password_hash` in its payload, and uses custom auth headers (`auth_token`) for subsequent requests, allowing a remote HTTP endpoint means credentials would be transmitted in plaintext across the internet, exposing them to interception.
**Learning:** When creating API clients that handle authentication credentials, we cannot assume the user will always provide a secure URL. While flexibility (like allowing custom base URLs for testing) is important, security defaults must fail-closed.
**Prevention:** Explicitly validate the scheme of the `base_url`. Enforce `https://` by raising a `ValueError` for `http://` connections unless the URL explicitly points to local testing environments (e.g., `localhost` or `127.0.0.1`).
