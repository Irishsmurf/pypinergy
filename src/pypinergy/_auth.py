"""Internal auth helpers."""

import hashlib


def hash_password(password: str) -> str:
    """Return the SHA-1 hex digest of *password*, as required by the Pinergy API.

    Args:
        password: The plaintext password.

    Returns:
        Lowercase hex-encoded SHA-1 digest string.
    """
    # SECURITY: Specify usedforsecurity=False to prevent crashes in FIPS-compliant environments
    # as SHA-1 is considered weak for cryptographic purposes, but required by the external API.
    return hashlib.sha1(password.encode(), usedforsecurity=False).hexdigest()
