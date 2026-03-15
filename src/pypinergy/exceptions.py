"""Exceptions raised by the pypinergy client."""


class PinergyError(Exception):
    """Base exception for all pypinergy errors."""


class PinergyAuthError(PinergyError):
    """Raised when authentication fails or the session has expired."""


class PinergyAPIError(PinergyError):
    """Raised when the API returns a non-success response.

    Attributes:
        error_code: The integer error code returned by the API.
        message: The human-readable error message from the API.
    """

    def __init__(self, message: str, error_code: int = 0) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message

    def __repr__(self) -> str:
        return f"PinergyAPIError(message={self.message!r}, error_code={self.error_code})"


class PinergyHTTPError(PinergyError):
    """Raised when an unexpected HTTP-level error occurs (e.g. 5xx, timeout)."""
