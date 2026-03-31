"""Internal auth helpers."""

import hashlib


def hash_password(password: str) -> str:
    """Return the SHA-1 hex digest of *password*, as required by the Pinergy API.

    Args:
        password: The plaintext password.

    Returns:
        Lowercase hex-encoded SHA-1 digest string.
    """
    # Explicitly mark usedforsecurity=False for FIPS compliance,
    # as the API requires SHA-1 and we cannot change the algorithm.
    return hashlib.sha1(password.encode(), usedforsecurity=False).hexdigest()
