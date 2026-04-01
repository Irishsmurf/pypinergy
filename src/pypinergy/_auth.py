"""Internal auth helpers."""

import hashlib


def hash_password(password: str) -> str:
    """Return the SHA-1 hex digest of *password*, as required by the Pinergy API.

    Args:
        password: The plaintext password.

    Returns:
        Lowercase hex-encoded SHA-1 digest string.
    """
    # use usedforsecurity=False for strict FIPS-compliant environments
    # since we are generating a hash required by an external API
    # and not doing something security-sensitive with it like signing a cert
    return hashlib.sha1(password.encode(), usedforsecurity=False).hexdigest()
