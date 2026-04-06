"""Internal auth helpers."""

import hashlib


def hash_password(password: str) -> str:
    """Return the SHA-1 hex digest of *password*, as required by the Pinergy API.

    Args:
        password: The plaintext password.

    Returns:
        Lowercase hex-encoded SHA-1 digest string.
    """
    # The Pinergy API requires SHA-1 for password hashing.
    # We specify usedforsecurity=False to ensure compatibility with FIPS-compliant environments.
    return hashlib.sha1(password.encode(), usedforsecurity=False).hexdigest()
