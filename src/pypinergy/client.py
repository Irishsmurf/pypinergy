"""Pinergy API client."""

from __future__ import annotations

from typing import Optional

import requests

from ._auth import hash_password
from .exceptions import PinergyAPIError, PinergyAuthError, PinergyHTTPError
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

    def request(self, method, url, *args, **kwargs):
        kwargs.setdefault("allow_redirects", False)
        return super().request(method, url, *args, **kwargs)


class PinergyClient:
    """Client for the Pinergy smart-meter API.

    Authentication is performed lazily — the first call to any API method that
    requires a token will trigger :meth:`login` automatically if no token has
    been set yet.

    Args:
        email: Registered Pinergy account email address.
        password: Plaintext account password (hashed internally before sending).
        base_url: Override the API base URL (useful for testing).
        timeout: Default request timeout in seconds.

    Example::

        from pypinergy import PinergyClient

        client = PinergyClient("user@example.com", "my-password")
        balance = client.get_balance()
        print(f"Balance: €{balance.credit_balance:.2f}")
    """

    def __init__(
        self,
        email: str,
        password: str,
        base_url: str = _BASE_URL,
        timeout: int = 30,
    ) -> None:
        self._email = email
        self._password_hash = hash_password(password)
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = _NoRedirectSession()
        self._session.headers.update({"User-Agent": _USER_AGENT})
        # Performance optimization: Managing _auth_token via property setter
        # directly syncs it to self._session.headers, avoiding repetitive
        # dictionary instantiations and merging on every API request.
        self.__auth_token: Optional[str] = None
        self._auth_token = None

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    @property
    def _auth_token(self) -> Optional[str]:
        return self.__auth_token

    @_auth_token.setter
    def _auth_token(self, value: Optional[str]) -> None:
        self.__auth_token = value
        if value is not None:
            self._session.headers["auth_token"] = value
        else:
            self._session.headers.pop("auth_token", None)

    @property
    def is_authenticated(self) -> bool:
        """True if an auth token is currently held."""
        return self._auth_token is not None

    def _ensure_auth(self) -> None:
        """Login if no token is present yet."""
        if not self.is_authenticated:
            self.login()

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    def _get(self, path: str) -> dict:
        """Perform an authenticated GET and return the parsed JSON body."""
        self._ensure_auth()
        try:
            response = self._session.get(
                self._url(path),
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 401:
                raise PinergyAuthError("Auth token rejected (401)") from exc
            raise PinergyHTTPError(str(exc)) from exc
        except requests.exceptions.RequestException as exc:
            raise PinergyHTTPError(str(exc)) from exc

        data = response.json()
        _raise_for_api_error(data)
        return data

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self) -> LoginResponse:
        """Authenticate with the Pinergy API and store the session token.

        Raises:
            PinergyAuthError: If credentials are invalid.
            PinergyHTTPError: On network-level errors.

        Returns:
            :class:`~pypinergy.models.LoginResponse` with full account details.
        """
        payload = {
            "email": self._email,
            "password": self._password_hash,
            "device_token": "",
        }
        try:
            response = self._session.post(
                self._url("/api/login/"),
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise PinergyHTTPError(str(exc)) from exc

        data = response.json()
        if not data.get("success"):
            raise PinergyAuthError(
                data.get("message", "Login failed") or "Login failed"
            )

        self._auth_token = data["auth_token"]
        return LoginResponse._from_dict(data)

    def logout(self) -> None:
        """Clear the stored auth token, effectively ending the session.

        Also clears the cached password hash so automatic re-login does not happen
        transparently after explicit logout.
        """
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
        try:
            response = self._session.get(
                self._url("/api/checkemail"),
                headers={"email_address": email},
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise PinergyHTTPError(str(exc)) from exc

        data = response.json()
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
        self._ensure_auth()
        payload = {
            "device_token": device_token,
            "device_type": device_type,
            "os_version": os_version,
        }
        try:
            response = self._session.post(
                self._url("/api/updatedevicetoken/"),
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise PinergyHTTPError(str(exc)) from exc

        data = response.json()
        _raise_for_api_error(data)
        return bool(data.get("success"))

    # ------------------------------------------------------------------
    # Version (unauthenticated)
    # ------------------------------------------------------------------

    def get_version(self) -> dict:
        """Return the raw version config JSON (unauthenticated).

        Returns:
            Parsed JSON dict from ``/version.json``.
        """
        try:
            response = self._session.get(
                self._url("/version.json"),
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise PinergyHTTPError(str(exc)) from exc
        return response.json()

    def __repr__(self) -> str:
        auth_status = "authenticated" if self.is_authenticated else "unauthenticated"
        return f"PinergyClient(email={self._email!r}, status={auth_status})"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _raise_for_api_error(data: dict) -> None:
    """Raise :class:`~pypinergy.exceptions.PinergyAPIError` if *data* signals failure."""
    if not data.get("success", True):
        raise PinergyAPIError(
            message=data.get("message") or "API returned an error",
            error_code=int(data.get("error_code", 0)),
        )
