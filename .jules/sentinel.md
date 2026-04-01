
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

## 2024-04-01 - [FIPS Compliance Failure via Unannotated SHA-1]
**Vulnerability:** The `hash_password` function used `hashlib.sha1` without `usedforsecurity=False` to generate a hash required for an external API. In FIPS-compliant environments, SHA-1 is blocked when used for security purposes, which causes the application to crash even when the hash is just a dumb requirement of an external API.
**Learning:** Python's `hashlib` in strict environments makes assumptions about the security intent of deprecated algorithms like MD5 or SHA-1. If an external API requires these hashes for non-critical functionality (e.g. legacy authentication handshakes), `hashlib` will block it unless explicitly told otherwise.
**Prevention:** When using deprecated algorithms like `hashlib.sha1` or `hashlib.md5` to satisfy external API requirements, always explicitly specify `usedforsecurity=False` to ensure compatibility with FIPS environments.
