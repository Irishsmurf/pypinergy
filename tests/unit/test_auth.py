"""Unit tests for the auth helper module."""

from pypinergy._auth import hash_password


def test_hash_password_returns_hex_string():
    result = hash_password("password")
    assert isinstance(result, str)
    assert all(c in "0123456789abcdef" for c in result)


def test_hash_password_known_value():
    # SHA-1("password") = 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8
    assert hash_password("password") == "5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8"


def test_hash_password_length():
    # SHA-1 always produces a 40-character hex digest
    assert len(hash_password("anything")) == 40
    assert len(hash_password("")) == 40


def test_hash_password_empty_string():
    # SHA-1("") = da39a3ee5e6b4b0d3255bfef95601890afd80709
    assert hash_password("") == "da39a3ee5e6b4b0d3255bfef95601890afd80709"


def test_hash_password_is_deterministic():
    assert hash_password("hello") == hash_password("hello")


def test_hash_password_different_inputs_differ():
    assert hash_password("abc") != hash_password("ABC")
