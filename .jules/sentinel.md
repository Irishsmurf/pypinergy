
## 2024-03-17 - [Authorization Bypass via Incomplete Logout]
**Vulnerability:** The `logout()` method only cleared `self._auth_token` but left `self._password_hash` intact. Because `PinergyClient` implements automatic lazy-login, an explicit `logout()` followed immediately by an authenticated API request would silently log the user back in using the cached password hash.
**Learning:** When implementing lazy-login or automatic re-authentication features, an explicit `logout` action must comprehensively destroy all state that enables the automatic flow. If credentials (even hashes) are cached for convenience, they must be purged upon explicit logout.
**Prevention:** Always trace the full lifecycle of authentication state. If `login()` relies on multiple state variables (token AND password hash), `logout()` must clear them all. Write explicit unit tests that verify consecutive `logout() -> API call` sequences throw `AuthError` instead of succeeding.

## 2024-03-18 - [Header Leakage via Cross-Origin Redirects in requests]
**Vulnerability:** The Pinergy API client uses custom HTTP headers for authentication (`auth_token`, `email_address`). The `requests` library automatically follows redirects by default, but it only strips standard authentication headers (like `Authorization`) on cross-origin redirects. Non-standard headers like `auth_token` and `email_address` are sent to the new origin, potentially leaking credentials to an attacker if the API ever redirects to a malicious site.
**Learning:** `requests` will leak custom authentication headers across domain boundaries. Standard libraries often don't provide the same security guarantees for custom implementations as they do for standard ones (e.g. `Authorization`).
**Prevention:** When using custom headers for authentication, always explicitly disable automatic redirects (`allow_redirects=False`) or implement custom redirect handling that explicitly strips sensitive headers before following cross-origin redirects.

## 2024-03-27 - [Plaintext Credential Leakage via Insecure Base URL]
**Vulnerability:** The API client permitted the use of insecure `http://` schema for its `base_url`, which would transmit API requests and custom authentication headers in plaintext.
**Learning:** Security controls like HTTPS must be explicitly enforced in API clients, not just assumed by default. Furthermore, when providing exceptions for local development/testing environments, naive string matching (like checking if the URL starts with "http://localhost") can be bypassed via subdomains (e.g. `http://localhost.example.com`).
**Prevention:** Always validate the `base_url` scheme and enforce `https://`. When whitelisting local testing environments, use a robust URL parsing library (`urllib.parse.urlparse`) to ensure that only exact hostnames like `localhost` or `127.0.0.1` are permitted.

## 2024-03-28 - [FIPS Compliance Failure via Unmarked SHA-1 Hash]
**Vulnerability:** The application used `hashlib.sha1` for API authentication payloads without explicitly marking it as `usedforsecurity=False`. In strict FIPS-compliant environments, Python blocks the use of MD5 and SHA-1 unless explicitly told it's not being used for a local security feature (like hashing a local password for storage). Here, SHA-1 is just an external API integration requirement, so it is safe and necessary to bypass the restriction.
**Learning:** Always specify `usedforsecurity=False` when using outdated hash functions (MD5, SHA-1) that are required for external API compatibility. If omitted, the application will crash on initialization in environments enforcing FIPS standards.
**Prevention:** Audit all uses of `hashlib` for older algorithms and explicitly add `usedforsecurity=False` where the hash is generated to satisfy external/legacy APIs rather than internal security functions.
