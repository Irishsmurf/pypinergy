"""Internal auth helpers."""

import hashlib


def hash_password(password: str) -> str:
    """Return the SHA-1 hex digest of *password*, as required by the Pinergy API.

    Args:
        password: The plaintext password.

    Returns:
        Lowercase hex-encoded SHA-1 digest string.
    """
    return hashlib.sha1(password.encode()).hexdigest()
