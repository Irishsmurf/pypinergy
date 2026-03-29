"""Internal auth helpers."""

import hashlib


def hash_password(password: str) -> str:
    """Return the SHA-1 hex digest of *password*, as required by the Pinergy API.

    Args:
        password: The plaintext password.

    Returns:
        Lowercase hex-encoded SHA-1 digest string.
    """
    # Use usedforsecurity=False to prevent crashes in strict FIPS-compliant
    # environments, as the API mandates SHA-1 for authentication.
    return hashlib.sha1(password.encode(), usedforsecurity=False).hexdigest()
