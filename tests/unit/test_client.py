"""Unit tests for PinergyClient — all HTTP calls are mocked with `responses`."""

import pytest
import requests
import responses as rsps_lib

from pypinergy import PinergyClient
from pypinergy.exceptions import PinergyAPIError, PinergyAuthError, PinergyHTTPError
from pypinergy.models import (
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
from tests.conftest import (
    ACTIVE_TOPUPS_PAYLOAD,
    BALANCE_PAYLOAD,
    COMPARE_PAYLOAD,
    CONFIG_PAYLOAD,
    DEFAULTS_PAYLOAD,
    LEVEL_PAY_PAYLOAD,
    LOGIN_PAYLOAD,
    NOTIF_PAYLOAD,
    USAGE_PAYLOAD,
)

BASE = "https://api.pinergy.ie"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_login(rsps, payload=None):
    rsps.add(
        rsps_lib.POST,
        f"{BASE}/api/login/",
        json=payload or LOGIN_PAYLOAD,
        status=200,
    )


def _make_client():
    return PinergyClient("user@example.com", "secret", base_url=BASE)


# ---------------------------------------------------------------------------
# Client initialisation
# ---------------------------------------------------------------------------


def test_client_repr_unauthenticated():
    client = _make_client()
    assert "unauthenticated" in repr(client)
    assert "user@example.com" in repr(client)


def test_client_is_authenticated_false_initially():
    assert not _make_client().is_authenticated


def test_client_does_not_store_plaintext_password():
    password = "secret-password"
    client = PinergyClient("user@example.com", password, base_url=BASE)
    assert not hasattr(client, "_password")
    assert hasattr(client, "_password_hash")
    # Ensure the plaintext password is not in the object's dictionary at all
    assert password not in client.__dict__.values()


def test_base_url_requires_https_remote():
    with pytest.raises(ValueError, match="base_url must use https://"):
        PinergyClient("user@example.com", "pass", base_url="http://api.pinergy.ie")


def test_base_url_allows_http_localhost():
    # Should not raise
    PinergyClient("user@example.com", "pass", base_url="http://localhost:8080")
    PinergyClient("user@example.com", "pass", base_url="http://127.0.0.1:5000")
    PinergyClient("user@example.com", "pass", base_url="http://[::1]:5000")


def test_base_url_blocks_localhost_bypass():
    with pytest.raises(ValueError, match="base_url must use https://"):
        PinergyClient(
            "user@example.com", "pass", base_url="http://localhost.example.com"
        )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_login_success():
    _add_login(rsps_lib)
    client = _make_client()
    result = client.login()

    assert isinstance(result, LoginResponse)
    assert result.auth_token == "TESTTOKEN123"
    assert client.is_authenticated
    assert "authenticated" in repr(client)


@rsps_lib.activate
def test_login_sends_sha1_password():
    _add_login(rsps_lib)
    client = _make_client()
    client.login()

    request_body = rsps_lib.calls[0].request.body
    import json

    body = json.loads(request_body)
    # "secret" SHA-1 = e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4
    assert body["password"] == "e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4"
    assert body["email"] == "user@example.com"


@rsps_lib.activate
def test_login_failure_raises_auth_error():
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE}/api/login/",
        json={"success": False, "error_code": 1, "message": "Invalid credentials"},
        status=200,
    )
    client = _make_client()
    with pytest.raises(PinergyAuthError, match="Invalid credentials"):
        client.login()


@rsps_lib.activate
def test_login_http_error_raises_http_error():
    rsps_lib.add(rsps_lib.POST, f"{BASE}/api/login/", status=500)
    client = _make_client()
    with pytest.raises(PinergyHTTPError):
        client.login()


@rsps_lib.activate
def test_logout_clears_token():
    _add_login(rsps_lib)
    client = _make_client()
    client.login()
    assert client.is_authenticated
    client.logout()
    assert not client.is_authenticated


# ---------------------------------------------------------------------------
# Auto-login on first request
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_auto_login_triggered_on_first_request():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", json=BALANCE_PAYLOAD, status=200)

    client = _make_client()
    assert not client.is_authenticated
    client.get_balance()
    assert client.is_authenticated
    # First call should have been a POST to /api/login/
    assert rsps_lib.calls[0].request.method == "POST"
    assert "/api/login/" in rsps_lib.calls[0].request.url


# ---------------------------------------------------------------------------
# check_email
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_check_email_registered():
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/checkemail",
        json={"success": True, "message": "", "error_code": 0},
        status=200,
    )
    client = _make_client()
    assert client.check_email("user@example.com") is True


@rsps_lib.activate
def test_check_email_not_registered():
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/checkemail",
        json={"success": False, "message": "Not found", "error_code": 1},
        status=200,
    )
    client = _make_client()
    assert client.check_email("nobody@example.com") is False


@rsps_lib.activate
def test_check_email_sends_header():
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/checkemail",
        json={"success": True, "message": "", "error_code": 0},
        status=200,
    )
    client = _make_client()
    client.check_email("test@example.com")
    assert rsps_lib.calls[0].request.headers["email_address"] == "test@example.com"


def test_check_email_rejects_crlf():
    client = _make_client()
    with pytest.raises(
        ValueError, match="Invalid email address: contains control characters"
    ):
        client.check_email("test\r\n@example.com")


# ---------------------------------------------------------------------------
# get_usage
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_get_usage():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/usage/", json=USAGE_PAYLOAD, status=200)
    result = _make_client().get_usage()
    assert isinstance(result, UsageResponse)
    assert len(result.day) == 2
    assert len(result.week) == 1


@rsps_lib.activate
def test_get_usage_sends_auth_token():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/usage/", json=USAGE_PAYLOAD, status=200)
    _make_client().get_usage()
    auth_call = rsps_lib.calls[1]
    assert auth_call.request.headers["auth_token"] == "TESTTOKEN123"


# ---------------------------------------------------------------------------
# get_level_pay_usage
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_get_level_pay_usage():
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET, f"{BASE}/api/levelpayusage/", json=LEVEL_PAY_PAYLOAD, status=200
    )
    result = _make_client().get_level_pay_usage()
    assert isinstance(result, LevelPayUsageResponse)
    assert result.labels == ["00:00", "00:30", "01:00"]


# ---------------------------------------------------------------------------
# get_balance
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_get_balance():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", json=BALANCE_PAYLOAD, status=200)
    result = _make_client().get_balance()
    assert isinstance(result, BalanceResponse)
    assert result.credit_balance == pytest.approx(16.38)
    assert result.top_up_in_days == 6


# ---------------------------------------------------------------------------
# get_active_topups
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_get_active_topups():
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/activetopups/",
        json=ACTIVE_TOPUPS_PAYLOAD,
        status=200,
    )
    result = _make_client().get_active_topups()
    assert isinstance(result, ActiveTopUpsResponse)
    assert len(result.scheduled) == 1


# ---------------------------------------------------------------------------
# compare_usage
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_compare_usage():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/compare/", json=COMPARE_PAYLOAD, status=200)
    result = _make_client().compare_usage()
    assert isinstance(result, CompareResponse)
    assert result.day.available is True


# ---------------------------------------------------------------------------
# get_config_info
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_get_config_info():
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET, f"{BASE}/api/configinfo/", json=CONFIG_PAYLOAD, status=200
    )
    result = _make_client().get_config_info()
    assert isinstance(result, ConfigInfoResponse)
    assert result.thresholds == [5]


# ---------------------------------------------------------------------------
# get_defaults_info
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_get_defaults_info():
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET, f"{BASE}/api/defaultsinfo/", json=DEFAULTS_PAYLOAD, status=200
    )
    result = _make_client().get_defaults_info()
    assert isinstance(result, DefaultsInfoResponse)
    assert len(result.house_types) == 3


# ---------------------------------------------------------------------------
# get_notification_preferences
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_get_notification_preferences():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/getnotif/", json=NOTIF_PAYLOAD, status=200)
    result = _make_client().get_notification_preferences()
    assert isinstance(result, NotificationPreferences)
    assert result.email is True
    assert result.sms is False


# ---------------------------------------------------------------------------
# update_device_token
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_update_device_token():
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE}/api/updatedevicetoken/",
        json={"success": True},
        status=200,
    )
    result = _make_client().update_device_token("fcm-token-xyz")
    assert result is True


@rsps_lib.activate
def test_update_device_token_sends_payload():
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE}/api/updatedevicetoken/",
        json={"success": True},
        status=200,
    )
    _make_client().update_device_token(
        "my-token", device_type="android", os_version="13"
    )

    import json

    body = json.loads(rsps_lib.calls[1].request.body)
    assert body["device_token"] == "my-token"
    assert body["device_type"] == "android"
    assert body["os_version"] == "13"


# ---------------------------------------------------------------------------
# get_version (unauthenticated)
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_get_version():
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/version.json",
        json={"min_version": "3.0.0", "force_update": False},
        status=200,
    )
    client = _make_client()
    result = client.get_version()
    assert result["min_version"] == "3.0.0"
    assert not client.is_authenticated  # should NOT have triggered login


# ---------------------------------------------------------------------------
# API error propagation
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_api_error_raises_pinergy_api_error():
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/balance/",
        json={"success": False, "error_code": 99, "message": "Something went wrong"},
        status=200,
    )
    client = _make_client()
    with pytest.raises(PinergyAPIError) as exc_info:
        client.get_balance()
    assert exc_info.value.error_code == 99
    assert "Something went wrong" in str(exc_info.value)


@rsps_lib.activate
def test_http_error_raises_pinergy_http_error():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", status=503)
    with pytest.raises(PinergyHTTPError):
        _make_client().get_balance()


@rsps_lib.activate
def test_401_raises_auth_error():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", status=401)
    with pytest.raises(PinergyAuthError):
        _make_client().get_balance()


# ---------------------------------------------------------------------------
# User-Agent header
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_user_agent_header_sent():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", json=BALANCE_PAYLOAD, status=200)
    _make_client().get_balance()
    assert rsps_lib.calls[1].request.headers["User-Agent"] == "okhttp/5.1.0"


# ---------------------------------------------------------------------------
# PinergyAPIError __repr__ — exceptions.py line 26
# ---------------------------------------------------------------------------


def test_pinergy_api_error_repr():
    err = PinergyAPIError(message="quota exceeded", error_code=42)
    assert repr(err) == "PinergyAPIError(message='quota exceeded', error_code=42)"


# ---------------------------------------------------------------------------
# RequestException (connection-level) paths — client.py lines not yet covered
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_get_raises_http_error_on_connection_error():
    """_get() RequestException branch (lines 95-96)."""
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/balance/",
        body=requests.exceptions.ConnectionError("network failure"),
    )
    with pytest.raises(PinergyHTTPError, match="network failure"):
        _make_client().get_balance()


@rsps_lib.activate
def test_login_raises_http_error_on_connection_error():
    """login() RequestException branch (lines 130-131)."""
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE}/api/login/",
        body=requests.exceptions.ConnectionError("no route to host"),
    )
    with pytest.raises(PinergyHTTPError, match="no route to host"):
        _make_client().login()


@rsps_lib.activate
def test_check_email_raises_http_error_on_connection_error():
    """check_email() RequestException branch (lines 164-165)."""
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/checkemail",
        body=requests.exceptions.ConnectionError("timeout"),
    )
    with pytest.raises(PinergyHTTPError, match="timeout"):
        _make_client().check_email("x@example.com")


@rsps_lib.activate
def test_update_device_token_raises_http_error_on_connection_error():
    """update_device_token() RequestException branch (lines 316-317)."""
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE}/api/updatedevicetoken/",
        body=requests.exceptions.ConnectionError("connection refused"),
    )
    with pytest.raises(PinergyHTTPError, match="connection refused"):
        _make_client().update_device_token("tok")


@rsps_lib.activate
def test_get_version_raises_http_error_on_connection_error():
    """get_version() RequestException branch (lines 339-340)."""
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/version.json",
        body=requests.exceptions.ConnectionError("dns failure"),
    )
    with pytest.raises(PinergyHTTPError, match="dns failure"):
        _make_client().get_version()


@rsps_lib.activate
def test_get_raises_http_error_on_timeout():
    """_get() RequestException branch for timeout (lines 95-96)."""
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/balance/",
        body=requests.exceptions.Timeout("Read timed out"),
    )
    with pytest.raises(PinergyHTTPError, match="Read timed out"):
        _make_client().get_balance()
