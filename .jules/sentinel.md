
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

## 2024-04-15 - [HTTP Header Injection via Custom Headers]
**Vulnerability:** The API client passed user-provided email addresses directly into custom HTTP headers (`email_address: user@example.com`) without validation. `requests` does not natively block `\r` or `\n` characters in headers unless specifically handled, allowing for CRLF (HTTP Header) Injection.
**Learning:** Even though underlying HTTP libraries sometimes block CRLF injections with generic exceptions, relying on them introduces unhandled exceptions or unpredictable application behavior. User inputs inserted directly into HTTP headers must be strictly validated at the application boundary to reject control characters like `\r` and `\n`.
**Prevention:** Always validate and sanitize user input before passing it into HTTP headers. Reject inputs containing `\r` or `\n` explicitly at the client or application layer by raising a clear, predictable `ValueError` before making the network request.
