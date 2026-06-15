"""Pinergy API client."""

from __future__ import annotations

import threading
import urllib.parse
from types import TracebackType
from typing import Any, Dict, Optional, Type

import requests

from ._auth import hash_password
from .exceptions import (
    PinergyAPIError,
    PinergyAuthError,
    PinergyHTTPError,
    PinergyResponseError,
    PinergyTimeoutError,
)
from .models import (
    ActiveTopUpsResponse,
    BalanceResponse,
    CompareResponse,
    ConfigInfoResponse,
    DefaultsInfoResponse,
    LevelPayUsageResponse,
    LoginResponse,
    NotificationPreferences,
    UsageResponse,
)

_BASE_URL = "https://api.pinergy.ie"
_USER_AGENT = "okhttp/5.1.0"


class _NoRedirectSession(requests.Session):
    """A requests Session that disables redirects by default to prevent header leakage."""

    def request(  # type: ignore[override]
        self, method: str, url: str, *args: Any, **kwargs: Any
    ) -> requests.Response:
        kwargs.setdefault("allow_redirects", False)
        return super().request(method, url, *args, **kwargs)


class PinergyClient:
    """Client for the Pinergy smart-meter API.

    Authentication is performed lazily — the first call to any API method that
    requires a token will trigger :meth:`login` automatically if no token has
    been set yet. Lazy login is thread-safe: concurrent first calls perform a
    single login. If the server rejects a token (HTTP 401), the stale token is
    dropped so the next call re-authenticates transparently.

    The client owns a pooled :class:`requests.Session` (keep-alive connection
    reuse). Use it as a context manager, or call :meth:`close` when done, to
    release the pool deterministically::

        with PinergyClient("user@example.com", "my-password") as client:
            balance = client.get_balance()
            print(f"Balance: €{balance.credit_balance:.2f}")

    Args:
        email: Registered Pinergy account email address.
        password: Plaintext account password (hashed internally before sending).
        base_url: Override the API base URL (useful for testing).
        timeout: Default request timeout in seconds, applied to every network
            call. Accepts a float for sub-second precision.
    """

    def __init__(
        self,
        email: str,
        password: str,
        base_url: str = _BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self._email = email
        self._password_hash: Optional[str] = hash_password(password)
        self._base_url = base_url.rstrip("/")

        parsed = urllib.parse.urlparse(self._base_url)
        if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError(
                "base_url must use https:// to prevent credential leakage "
                "(except for localhost/127.0.0.1/::1)"
            )

        self._timeout = timeout
        self._auth_token: Optional[str] = None
        # Reentrant: _ensure_auth() holds it while calling login(), which takes it again.
        self._auth_lock = threading.RLock()
        self._session = _NoRedirectSession()
        self._session.headers.update({"User-Agent": _USER_AGENT})

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Release the underlying HTTP connection pool.

        Idempotent — safe to call more than once. The client must not be used
        for further API calls after closing.
        """
        self._session.close()

    def __enter__(self) -> "PinergyClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    @property
    def is_authenticated(self) -> bool:
        """True if an auth token is currently held."""
        return self._auth_token is not None

    def _ensure_auth(self) -> None:
        """Login if no token is present yet (thread-safe, double-checked)."""
        if self._auth_token is None:
            with self._auth_lock:
                if self._auth_token is None:
                    self.login()

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        authenticated: bool = False,
        check_api_error: bool = True,
    ) -> Dict[str, Any]:
        """Perform an HTTP request and return the parsed JSON body.

        Every transport failure is mapped onto the ``PinergyError`` hierarchy:

        - timeout → :class:`PinergyTimeoutError`
        - HTTP 401 on an authenticated call → :class:`PinergyAuthError`
          (the stale token is also dropped so the next call re-authenticates)
        - token rejection reported as HTTP 200 ``success: false`` on an
          authenticated call → :class:`PinergyAuthError` (stale token dropped
          likewise)
        - other HTTP / network errors → :class:`PinergyHTTPError`
        - unparseable or non-object JSON body → :class:`PinergyResponseError`
        - other application-level ``success: false`` → :class:`PinergyAPIError`
          (unless *check_api_error* is False)
        """
        attempts = 2 if authenticated else 1

        for attempt in range(attempts):
            req_headers = dict(headers) if headers else {}
            if authenticated:
                self._ensure_auth()
                req_headers["auth_token"] = self._auth_token or ""

            token_used = self._auth_token

            try:
                response = self._session.request(
                    method,
                    self._url(path),
                    json=json,
                    headers=req_headers,
                    timeout=self._timeout,
                )
                response.raise_for_status()
            except requests.exceptions.Timeout as exc:
                raise PinergyTimeoutError(str(exc)) from exc
            except requests.exceptions.HTTPError as exc:
                if authenticated and exc.response is not None and exc.response.status_code == 401:
                    with self._auth_lock:
                        if self._auth_token == token_used:
                            self._auth_token = None
                    if attempt < attempts - 1 and self._password_hash is not None:
                        continue
                    raise PinergyAuthError("Auth token rejected (401)") from exc
                raise PinergyHTTPError(str(exc)) from exc
            except requests.exceptions.RequestException as exc:
                raise PinergyHTTPError(str(exc)) from exc

            try:
                data = response.json()
            except ValueError as exc:
                raise PinergyResponseError(f"API returned malformed JSON: {exc}") from exc
            if not isinstance(data, dict):
                raise PinergyResponseError(f"API returned non-object JSON ({type(data).__name__})")

            if check_api_error:
                if authenticated and not data.get("success", True):
                    message = str(data.get("message") or "")
                    if _is_token_rejection(message):
                        with self._auth_lock:
                            if self._auth_token == token_used:
                                self._auth_token = None
                        if attempt < attempts - 1 and self._password_hash is not None:
                            continue
                        raise PinergyAuthError(message or "Auth token rejected")
                _raise_for_api_error(data)
            return data

    def _get(self, path: str) -> Dict[str, Any]:
        """Perform an authenticated GET and return the parsed JSON body."""
        return self._request("GET", path, authenticated=True)

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self) -> LoginResponse:
        """Authenticate with the Pinergy API and store the session token.

        Thread-safe — concurrent callers serialize on an internal lock.

        Raises:
            PinergyAuthError: If credentials are invalid, or this client was
                explicitly logged out (credentials are discarded on
                :meth:`logout`; create a new client to re-authenticate).
            PinergyTimeoutError: If the request times out.
            PinergyHTTPError: On network-level errors.
            PinergyResponseError: If the response body is malformed or is
                missing the ``auth_token``.

        Returns:
            :class:`~pypinergy.models.LoginResponse` with full account details.
        """
        with self._auth_lock:
            if self._password_hash is None:
                raise PinergyAuthError(
                    "Client has been logged out — credentials were discarded; "
                    "create a new PinergyClient to re-authenticate"
                )
            payload = {
                "email": self._email,
                "password": self._password_hash,
                "device_token": "",
            }
            data = self._request("POST", "/api/login/", json=payload, check_api_error=False)
            if not data.get("success"):
                raise PinergyAuthError(data.get("message", "Login failed") or "Login failed")

            token = data.get("auth_token")
            if not isinstance(token, str) or not token:
                raise PinergyResponseError(
                    "Login succeeded but the response did not include an auth_token"
                )
            self._auth_token = token
            return LoginResponse._from_dict(data)

    def logout(self) -> None:
        """Clear the stored auth token, effectively ending the session.

        Also clears the cached password hash so automatic re-login does not happen
        transparently after explicit logout. Subsequent API calls raise
        :class:`PinergyAuthError` immediately, without touching the network.
        """
        with self._auth_lock:
            self._auth_token = None
            self._password_hash = None

    def check_email(self, email: str) -> bool:
        """Check whether an email address has a registered Pinergy account.

        This endpoint does **not** require authentication.

        Args:
            email: Email address to check.

        Returns:
            True if the address is registered.
        """
        if "\r" in email or "\n" in email:
            raise ValueError("Email address cannot contain carriage return or line feed characters")
        data = self._request(
            "GET",
            "/api/checkemail",
            headers={"email_address": email},
            check_api_error=False,
        )
        return bool(data.get("success"))

    # ------------------------------------------------------------------
    # Usage
    # ------------------------------------------------------------------

    def get_usage(self) -> UsageResponse:
        """Return daily, weekly, and monthly aggregated usage.

        Returns:
            :class:`~pypinergy.models.UsageResponse` with ``day``, ``week``,
            and ``month`` lists of :class:`~pypinergy.models.UsageEntry`.

        Example::

            usage = client.get_usage()
            for entry in usage.day:
                print(f"{entry.date:%Y-%m-%d}  {entry.kwh:.2f} kWh  €{entry.amount:.2f}")
        """
        return UsageResponse._from_dict(self._get("/api/usage/"))

    def get_level_pay_usage(self) -> LevelPayUsageResponse:
        """Return half-hourly interval data for level-pay customers.

        Returns:
            :class:`~pypinergy.models.LevelPayUsageResponse`
        """
        return LevelPayUsageResponse._from_dict(self._get("/api/levelpayusage/"))

    # ------------------------------------------------------------------
    # Balance
    # ------------------------------------------------------------------

    def get_balance(self) -> BalanceResponse:
        """Return the current credit balance and meter status.

        Returns:
            :class:`~pypinergy.models.BalanceResponse`

        Example::

            bal = client.get_balance()
            print(f"€{bal.credit_balance:.2f} — {bal.top_up_in_days} days remaining")
            if bal.credit_low:
                print("Warning: credit is low!")
        """
        return BalanceResponse._from_dict(self._get("/api/balance/"))

    # ------------------------------------------------------------------
    # Top-ups
    # ------------------------------------------------------------------

    def get_active_topups(self) -> ActiveTopUpsResponse:
        """Return scheduled and automatic top-up configurations.

        Returns:
            :class:`~pypinergy.models.ActiveTopUpsResponse`
        """
        return ActiveTopUpsResponse._from_dict(self._get("/api/activetopups/"))

    # ------------------------------------------------------------------
    # Compare
    # ------------------------------------------------------------------

    def compare_usage(self) -> CompareResponse:
        """Compare this home's usage with similar homes.

        Returns:
            :class:`~pypinergy.models.CompareResponse` with ``day``, ``week``,
            and ``month`` :class:`~pypinergy.models.ComparePeriod` objects.

        Example::

            cmp = client.compare_usage()
            d = cmp.day
            print(f"Today: {d.kwh.users_home:.1f} kWh vs avg {d.kwh.average_home:.1f} kWh")
        """
        return CompareResponse._from_dict(self._get("/api/compare/"))

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def get_config_info(self) -> ConfigInfoResponse:
        """Return valid top-up amounts and alert thresholds.

        Returns:
            :class:`~pypinergy.models.ConfigInfoResponse`
        """
        return ConfigInfoResponse._from_dict(self._get("/api/configinfo/"))

    def get_defaults_info(self) -> DefaultsInfoResponse:
        """Return reference data for house and heating types.

        Returns:
            :class:`~pypinergy.models.DefaultsInfoResponse`
        """
        return DefaultsInfoResponse._from_dict(self._get("/api/defaultsinfo/"))

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def get_notification_preferences(self) -> NotificationPreferences:
        """Return the account's notification channel preferences.

        Returns:
            :class:`~pypinergy.models.NotificationPreferences`
        """
        return NotificationPreferences._from_dict(self._get("/api/getnotif/"))

    # ------------------------------------------------------------------
    # Device
    # ------------------------------------------------------------------

    def update_device_token(
        self,
        device_token: str = "",
        device_type: str = "android",
        os_version: str = "",
    ) -> bool:
        """Register or update the FCM push-notification token.

        For headless / server-side use you can pass an empty string for
        *device_token* or skip this call entirely.

        Args:
            device_token: Firebase Cloud Messaging token.
            device_type: Platform string (e.g. ``"android"``).
            os_version: OS version string.

        Returns:
            True on success.
        """
        payload = {
            "device_token": device_token,
            "device_type": device_type,
            "os_version": os_version,
        }
        data = self._request("POST", "/api/updatedevicetoken/", json=payload, authenticated=True)
        return bool(data.get("success"))

    # ------------------------------------------------------------------
    # Version (unauthenticated)
    # ------------------------------------------------------------------

    def get_version(self) -> Dict[str, Any]:
        """Return the raw version config JSON (unauthenticated).

        Returns:
            Parsed JSON dict from ``/version.json``.
        """
        return self._request("GET", "/version.json", check_api_error=False)

    def __repr__(self) -> str:
        auth_status = "authenticated" if self.is_authenticated else "unauthenticated"
        return f"PinergyClient(email={self._email!r}, status={auth_status})"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_token_rejection(message: str) -> bool:
    """Return True if an API error message indicates a rejected auth token.

    The API reports an expired or invalid session token as HTTP 200 with
    ``success: false`` and a message like "Auth_token is not correct.".
    """
    lowered = message.lower()
    return "auth_token" in lowered or "auth token" in lowered


def _raise_for_api_error(data: Dict[str, Any]) -> None:
    """Raise :class:`~pypinergy.exceptions.PinergyAPIError` if *data* signals failure."""
    if not data.get("success", True):
        try:
            error_code = int(data.get("error_code") or 0)
        except (TypeError, ValueError):
            error_code = 0
        raise PinergyAPIError(
            message=data.get("message") or "API returned an error",
            error_code=error_code,
        )
