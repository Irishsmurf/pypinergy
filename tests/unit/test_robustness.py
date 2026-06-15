"""Unit tests for the hardening refactor.

Covers: session lifecycle (context manager / close), exception mapping for
timeouts and malformed payloads, thread-safe lazy authentication, 401
self-healing, post-logout fast-fail, defensive model parsing, and the
``*_dt`` alias properties.
"""

import threading
import time
from pathlib import Path

import pytest
import requests
import responses as rsps_lib

import pypinergy
from pypinergy import PinergyClient
from pypinergy.exceptions import (
    PinergyAuthError,
    PinergyError,
    PinergyHTTPError,
    PinergyResponseError,
    PinergyTimeoutError,
)
from pypinergy.models import (
    BalanceResponse,
    DefaultsInfoResponse,
    HeatingType,
    HouseType,
    LevelPayUsageResponse,
    LoginResponse,
    UsageEntry,
    UsageResponse,
)
from tests.conftest import BALANCE_PAYLOAD, LOGIN_PAYLOAD

BASE = "https://api.pinergy.ie"


def _add_login(rsps, payload=None):
    rsps.add(rsps_lib.POST, f"{BASE}/api/login/", json=payload or LOGIN_PAYLOAD, status=200)


def _make_client():
    return PinergyClient("user@example.com", "secret", base_url=BASE)


# ---------------------------------------------------------------------------
# Lifecycle: context manager and close()
# ---------------------------------------------------------------------------


def test_context_manager_returns_client_and_closes(monkeypatch):
    client = _make_client()
    closed = []
    monkeypatch.setattr(client._session, "close", lambda: closed.append(True))
    with client as ctx:
        assert ctx is client
        assert closed == []
    assert closed == [True]


def test_context_manager_closes_on_exception(monkeypatch):
    client = _make_client()
    closed = []
    monkeypatch.setattr(client._session, "close", lambda: closed.append(True))
    with pytest.raises(RuntimeError):
        with client:
            raise RuntimeError("boom")
    assert closed == [True]


def test_close_is_idempotent():
    client = _make_client()
    client.close()
    client.close()  # must not raise


# ---------------------------------------------------------------------------
# Exception mapping: timeouts
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_timeout_raises_timeout_error():
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/balance/",
        body=requests.exceptions.Timeout("Read timed out"),
    )
    with pytest.raises(PinergyTimeoutError, match="Read timed out"):
        _make_client().get_balance()


@rsps_lib.activate
def test_timeout_error_is_http_error_subclass():
    """Existing `except PinergyHTTPError` consumers must keep catching timeouts."""
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE}/api/login/",
        body=requests.exceptions.Timeout("timed out"),
    )
    with pytest.raises(PinergyHTTPError):
        _make_client().login()
    assert issubclass(PinergyTimeoutError, PinergyHTTPError)


# ---------------------------------------------------------------------------
# Exception mapping: malformed payloads
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_malformed_json_raises_response_error():
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/balance/",
        body="<html>not json</html>",
        status=200,
        content_type="application/json",
    )
    with pytest.raises(PinergyResponseError, match="malformed JSON"):
        _make_client().get_balance()


@rsps_lib.activate
def test_non_object_json_raises_response_error():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", json=[1, 2, 3], status=200)
    with pytest.raises(PinergyResponseError, match="non-object"):
        _make_client().get_balance()


@rsps_lib.activate
def test_login_missing_auth_token_raises_response_error():
    _add_login(rsps_lib, payload={"success": True})  # no auth_token key
    with pytest.raises(PinergyResponseError, match="auth_token"):
        _make_client().login()


def test_response_error_is_value_error_and_pinergy_error():
    """Callers catching ValueError (the raw json error) or PinergyError keep working."""
    assert issubclass(PinergyResponseError, ValueError)
    assert issubclass(PinergyResponseError, PinergyError)


# ---------------------------------------------------------------------------
# Auth: 401 self-healing, thread-safe lazy login, post-logout fast-fail
# ---------------------------------------------------------------------------


@rsps_lib.activate
def test_401_drops_stale_token_for_reauth():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", status=401)
    client = _make_client()
    client.login()
    assert client.is_authenticated
    with pytest.raises(PinergyAuthError):
        client.get_balance()
    # Stale token was dropped, so the next call will re-authenticate lazily.
    assert not client.is_authenticated


def test_concurrent_lazy_auth_logs_in_once(monkeypatch):
    client = _make_client()
    login_calls = []

    def fake_login():
        login_calls.append(1)
        time.sleep(0.05)  # widen the race window
        client._auth_token = "tok"

    monkeypatch.setattr(client, "login", fake_login)

    threads = [threading.Thread(target=client._ensure_auth) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(login_calls) == 1
    assert client.is_authenticated


def test_concurrent_self_healing_reauth(monkeypatch):
    client = _make_client()
    client._auth_token = "stale_token"

    lock = threading.Lock()
    login_calls = []
    def fake_login():
        with lock:
            login_calls.append(1)
        time.sleep(0.05)  # widen the race window
        client._auth_token = "new_token"
        return LoginResponse._from_dict({
            "success": True,
            "auth_token": "new_token",
            "user": None,
            "house": None,
            "credit_cards": None
        })

    monkeypatch.setattr(client, "login", fake_login)

    request_calls = []
    def fake_request(method, url, *args, **kwargs):
        headers = kwargs.get("headers", {})
        token = headers.get("auth_token")
        with lock:
            request_calls.append(token)

        resp = requests.Response()
        resp.url = url

        if token == "stale_token":
            resp.status_code = 401
            raise requests.exceptions.HTTPError("401 Client Error: Unauthorized for url", response=resp)
        elif token == "new_token":
            resp.status_code = 200
            resp._content = b'{"success": true, "balance": 10.0}'
            return resp
        else:
            resp.status_code = 500
            raise requests.exceptions.HTTPError("Unexpected token", response=resp)

    monkeypatch.setattr(client._session, "request", fake_request)

    results = []
    errors = []

    def run_get_balance():
        try:
            res = client.get_balance()
            with lock:
                results.append(res)
        except Exception as e:
            with lock:
                errors.append(e)

    threads = [threading.Thread(target=run_get_balance) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if errors:
        raise errors[0]
    assert len(errors) == 0
    assert len(results) == 5
    assert len(login_calls) == 1
    assert "stale_token" in request_calls
    assert "new_token" in request_calls


def test_concurrent_self_healing_reauth_api_payload(monkeypatch):
    client = _make_client()
    client._auth_token = "stale_token"

    lock = threading.Lock()
    login_calls = []
    def fake_login():
        with lock:
            login_calls.append(1)
        time.sleep(0.05)  # widen the race window
        client._auth_token = "new_token"
        return LoginResponse._from_dict({
            "success": True,
            "auth_token": "new_token",
            "user": None,
            "house": None,
            "credit_cards": None
        })

    monkeypatch.setattr(client, "login", fake_login)

    request_calls = []
    def fake_request(method, url, *args, **kwargs):
        headers = kwargs.get("headers", {})
        token = headers.get("auth_token")
        with lock:
            request_calls.append(token)

        resp = requests.Response()
        resp.url = url
        resp.status_code = 200

        if token == "stale_token":
            resp._content = b'{"success": false, "message": "Auth_token is not correct."}'
            return resp
        elif token == "new_token":
            resp._content = b'{"success": true, "balance": 10.0}'
            return resp
        else:
            resp.status_code = 500
            raise requests.exceptions.HTTPError("Unexpected token", response=resp)

    monkeypatch.setattr(client._session, "request", fake_request)

    results = []
    errors = []

    def run_get_balance():
        try:
            res = client.get_balance()
            with lock:
                results.append(res)
        except Exception as e:
            with lock:
                errors.append(e)

    threads = [threading.Thread(target=run_get_balance) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if errors:
        raise errors[0]
    assert len(errors) == 0
    assert len(results) == 5
    assert len(login_calls) == 1
    assert "stale_token" in request_calls
    assert "new_token" in request_calls


@rsps_lib.activate
def test_logout_fails_fast_without_network():
    _add_login(rsps_lib)
    client = _make_client()
    client.login()
    client.logout()
    # No GET mock is registered: if the client touched the network, responses
    # would raise a ConnectionError -> PinergyHTTPError, failing this test.
    with pytest.raises(PinergyAuthError, match="logged out"):
        client.get_balance()


@rsps_lib.activate
def test_update_device_token_401_raises_auth_error():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.POST, f"{BASE}/api/updatedevicetoken/", status=401)
    with pytest.raises(PinergyAuthError):
        _make_client().update_device_token("tok")


# ---------------------------------------------------------------------------
# Defensive model parsing: null / missing / wrong-typed fields
# ---------------------------------------------------------------------------


def test_login_response_tolerates_null_nested_objects():
    lr = LoginResponse._from_dict(
        {"success": True, "auth_token": "t", "user": None, "house": None, "credit_cards": None}
    )
    assert lr.user.name == ""
    assert lr.house.type == 0
    assert lr.credit_cards == []


def test_usage_entry_tolerates_null_and_junk_scalars():
    entry = UsageEntry._from_dict({"amount": None, "kwh": "abc", "co2": "1.5", "date": None})
    assert entry.amount == 0.0
    assert entry.kwh == 0.0
    assert entry.co2 == pytest.approx(1.5)
    assert entry.date_ts == 0


def test_usage_response_tolerates_null_buckets():
    ur = UsageResponse._from_dict({"day": None, "week": None, "month": None})
    assert ur.day == [] and ur.week == [] and ur.month == []


def test_level_pay_tolerates_null_usage_data():
    """The real login payload contains "usageData": null — must not AttributeError."""
    lp = LevelPayUsageResponse._from_dict({"usageData": None})
    assert lp.labels == [] and lp.flags == [] and lp.values == []


def test_level_pay_tolerates_corrupted_payloads():
    # usageData is dict but daily is None
    lp1 = LevelPayUsageResponse._from_dict({"usageData": {"daily": None}})
    assert lp1.labels == [] and lp1.flags == [] and lp1.values == []

    # daily has null labels/flags/values or values containing None
    lp2 = LevelPayUsageResponse._from_dict({
        "usageData": {
            "daily": {
                "labels": [None, "00:30"],
                "flags": [None, "Standard"],
                "values": [None, {"label": "14/03", "daykWh": None}]
            }
        }
    })
    assert lp2.labels == ["", "00:30"]
    assert lp2.flags == ["", "Standard"]
    assert len(lp2.values) == 1
    assert lp2.values[0].label == "14/03"
    assert lp2.values[0].day_kwh == {}


def test_balance_response_tolerates_nulls():
    br = BalanceResponse._from_dict({"balance": None, "top_up_in_days": None})
    assert br.credit_balance == 0.0
    assert br.top_up_in_days == 0


def test_house_and_heating_types_tolerate_missing_keys():
    assert HouseType._from_dict({}).id == 0
    assert HouseType._from_dict({}).name == ""
    assert HeatingType._from_dict({"id": "3"}).id == 3


def test_defaults_info_tolerates_null_lists():
    di = DefaultsInfoResponse._from_dict({"house_types": None, "heating_types": None})
    assert di.house_types == [] and di.heating_types == []


def test_user_coerces_non_string_scalars():
    from pypinergy.models import User

    user = User._from_dict({"title": 123, "name": None})
    assert user.title == "123"
    assert user.name == ""


@rsps_lib.activate
def test_api_error_with_non_numeric_error_code():
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/balance/",
        json={"success": False, "error_code": "not-a-number", "message": "oops"},
        status=200,
    )
    from pypinergy.exceptions import PinergyAPIError

    with pytest.raises(PinergyAPIError) as exc_info:
        _make_client().get_balance()
    assert exc_info.value.error_code == 0
    assert "oops" in str(exc_info.value)


# ---------------------------------------------------------------------------
# *_dt alias properties (convention-aligned names; old names stay supported)
# ---------------------------------------------------------------------------


def test_usage_entry_date_dt_alias():
    entry = UsageEntry._from_dict({"available": True, "date": "1773446400"})
    assert entry.date_dt == entry.date


def test_balance_dt_aliases():
    br = BalanceResponse._from_dict(BALANCE_PAYLOAD)
    assert br.last_top_up_dt == br.last_top_up_time
    assert br.last_reading_dt == br.last_reading


# ---------------------------------------------------------------------------
# Packaging: exports and version sync
# ---------------------------------------------------------------------------


def test_new_exceptions_exported_from_package_root():
    assert pypinergy.PinergyTimeoutError is PinergyTimeoutError
    assert pypinergy.PinergyResponseError is PinergyResponseError
    assert "PinergyTimeoutError" in pypinergy.__all__
    assert "PinergyResponseError" in pypinergy.__all__


def test_version_matches_pyproject():
    pyproject = Path(__file__).parents[2] / "pyproject.toml"
    assert f'version = "{pypinergy.__version__}"' in pyproject.read_text()
