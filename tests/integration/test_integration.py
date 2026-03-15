"""Integration tests — hit the real Pinergy API.

Test tiers
----------
``@pytest.mark.network``
    Hits the real API with **intentionally bad credentials**.  No secrets
    needed — just network access.  Run with::

        pytest tests/integration/ -m network -v

``@_SKIP`` (PINERGY_EMAIL + PINERGY_PASSWORD required)
    Tests that need a valid account.  Run with::

        PINERGY_EMAIL=you@example.com PINERGY_PASSWORD=secret \
            pytest tests/integration/ -v
"""

import os

import pytest

from pypinergy import PinergyClient
from pypinergy.exceptions import PinergyAuthError
from pypinergy.models import (
    ActiveTopUpsResponse,
    BalanceResponse,
    CompareResponse,
    ConfigInfoResponse,
    DefaultsInfoResponse,
    LoginResponse,
    NotificationPreferences,
    UsageResponse,
)

# ---------------------------------------------------------------------------
# Skip guards
# ---------------------------------------------------------------------------

_EMAIL = os.environ.get("PINERGY_EMAIL")
_PASSWORD = os.environ.get("PINERGY_PASSWORD")
_SKIP = pytest.mark.skipif(
    not (_EMAIL and _PASSWORD),
    reason="Set PINERGY_EMAIL and PINERGY_PASSWORD to run integration tests",
)

_BAD_EMAIL = "no-such-user-xyzzy@example.invalid"
_BAD_PASSWORD = "definitely-wrong-password-xyz123"


@pytest.fixture(scope="module")
def client():
    """Authenticated client shared across all integration tests in this module."""
    c = PinergyClient(_EMAIL or "", _PASSWORD or "")
    c.login()
    return c


# ---------------------------------------------------------------------------
# Login failures — network only, no valid credentials required
# ---------------------------------------------------------------------------


@pytest.mark.network
def test_login_unknown_email_raises_auth_error():
    """Completely unknown email returns success:false → PinergyAuthError."""
    c = PinergyClient(_BAD_EMAIL, _BAD_PASSWORD)
    with pytest.raises(PinergyAuthError):
        c.login()


@pytest.mark.network
def test_login_empty_password_raises_auth_error():
    """An empty password hash is rejected by the API."""
    c = PinergyClient(_BAD_EMAIL, "")
    with pytest.raises(PinergyAuthError):
        c.login()


@pytest.mark.network
def test_login_failure_does_not_store_token():
    """A failed login must not set auth_token — client stays unauthenticated."""
    c = PinergyClient(_BAD_EMAIL, _BAD_PASSWORD)
    with pytest.raises(PinergyAuthError):
        c.login()
    assert not c.is_authenticated
    assert c._auth_token is None


@pytest.mark.network
def test_login_error_message_is_non_empty():
    """The API error message must be preserved in the exception."""
    c = PinergyClient(_BAD_EMAIL, _BAD_PASSWORD)
    with pytest.raises(PinergyAuthError) as exc_info:
        c.login()
    assert str(exc_info.value).strip() != ""


@pytest.mark.network
def test_auto_login_failure_propagates_through_api_call():
    """When _ensure_auth() triggers login() and that fails, the caller sees PinergyAuthError."""
    c = PinergyClient(_BAD_EMAIL, _BAD_PASSWORD)
    # get_balance() internally calls _ensure_auth() → login() → raises
    with pytest.raises(PinergyAuthError):
        c.get_balance()
    assert not c.is_authenticated


@pytest.mark.network
def test_repeated_login_failures_stay_unauthenticated():
    """Calling login() multiple times with bad creds never authenticates."""
    c = PinergyClient(_BAD_EMAIL, _BAD_PASSWORD)
    for _ in range(2):
        with pytest.raises(PinergyAuthError):
            c.login()
        assert not c.is_authenticated


# ---------------------------------------------------------------------------
# Login failures — valid email, wrong password (requires PINERGY_EMAIL)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _EMAIL, reason="Set PINERGY_EMAIL to run this test")
def test_login_wrong_password_raises_auth_error():
    """Correct email + wrong password is rejected → PinergyAuthError."""
    c = PinergyClient(_EMAIL, _BAD_PASSWORD)
    with pytest.raises(PinergyAuthError):
        c.login()


@pytest.mark.skipif(not _EMAIL, reason="Set PINERGY_EMAIL to run this test")
def test_login_wrong_password_does_not_store_token():
    """Wrong password must not store a token even when email is valid."""
    c = PinergyClient(_EMAIL, _BAD_PASSWORD)
    with pytest.raises(PinergyAuthError):
        c.login()
    assert not c.is_authenticated
    assert c._auth_token is None


@_SKIP
def test_failed_relogin_preserves_existing_token(client):
    """A failed login() call on an already-authenticated client must not clear the token."""
    assert client.is_authenticated
    good_token = client._auth_token

    # Inject the good token into a new client, then attempt login with bad creds
    imposter = PinergyClient(_EMAIL, _BAD_PASSWORD)
    imposter._auth_token = good_token

    with pytest.raises(PinergyAuthError):
        imposter.login()

    # Token must be preserved — not None'd out on failure
    assert imposter._auth_token == good_token
    assert imposter.is_authenticated


# ---------------------------------------------------------------------------
# Auth — successful login
# ---------------------------------------------------------------------------


@_SKIP
def test_login_returns_auth_token(client):
    assert client.is_authenticated
    assert isinstance(client._auth_token, str)
    assert len(client._auth_token) > 0


@_SKIP
def test_check_email_registered(client):
    result = client.check_email(_EMAIL)
    assert result is True


@_SKIP
def test_check_email_unknown():
    c = PinergyClient(_EMAIL, _PASSWORD)
    result = c.check_email("definitely-not-registered-xyzzy@example.invalid")
    assert result is False


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------


@_SKIP
def test_get_usage_returns_data(client):
    usage = client.get_usage()
    assert isinstance(usage, UsageResponse)
    # API spec says 7 day entries, 8 week, 11 month — check at least some data
    assert len(usage.day) > 0
    assert len(usage.week) > 0
    assert len(usage.month) > 0


@_SKIP
def test_usage_entry_has_valid_amounts(client):
    usage = client.get_usage()
    for entry in usage.day:
        assert entry.kwh >= 0
        assert entry.amount >= 0


@_SKIP
def test_usage_entries_have_utc_datetimes(client):
    from datetime import timezone
    usage = client.get_usage()
    for entry in usage.day:
        assert entry.date.tzinfo is timezone.utc


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------


@_SKIP
def test_get_balance(client):
    bal = client.get_balance()
    assert isinstance(bal, BalanceResponse)
    assert isinstance(bal.balance, float)
    assert bal.top_up_in_days >= 0


@_SKIP
def test_balance_power_off_is_bool(client):
    bal = client.get_balance()
    assert isinstance(bal.power_off, bool)


# ---------------------------------------------------------------------------
# Active top-ups
# ---------------------------------------------------------------------------


@_SKIP
def test_get_active_topups(client):
    result = client.get_active_topups()
    assert isinstance(result, ActiveTopUpsResponse)
    assert isinstance(result.scheduled, list)
    assert isinstance(result.auto_top_ups, list)


# ---------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------


@_SKIP
def test_compare_usage(client):
    result = client.compare_usage()
    assert isinstance(result, CompareResponse)
    assert result.day.kwh.users_home >= 0
    assert result.day.kwh.average_home >= 0


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@_SKIP
def test_get_config_info(client):
    result = client.get_config_info()
    assert isinstance(result, ConfigInfoResponse)
    assert len(result.top_up_amounts) > 0
    assert all(isinstance(a, int) for a in result.top_up_amounts)


@_SKIP
def test_get_defaults_info(client):
    result = client.get_defaults_info()
    assert isinstance(result, DefaultsInfoResponse)
    assert len(result.house_types) > 0
    assert len(result.heating_types) > 0


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


@_SKIP
def test_get_notification_preferences(client):
    result = client.get_notification_preferences()
    assert isinstance(result, NotificationPreferences)
    assert isinstance(result.email, bool)
    assert isinstance(result.sms, bool)


# ---------------------------------------------------------------------------
# Version (unauthenticated)
# ---------------------------------------------------------------------------


@_SKIP
def test_get_version():
    c = PinergyClient(_EMAIL or "", _PASSWORD or "")
    result = c.get_version()
    assert isinstance(result, dict)
    assert not c.is_authenticated  # version endpoint should not trigger login
