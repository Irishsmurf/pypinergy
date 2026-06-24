"""Unit tests for automatic retries with exponential backoff (#197)."""

import pytest
import requests
import responses as rsps_lib

from pypinergy import PinergyClient
from pypinergy.exceptions import PinergyHTTPError
from tests.conftest import LOGIN_PAYLOAD

BASE = "https://api.pinergy.ie"


def _add_login(rsps):
    rsps.add(rsps_lib.POST, f"{BASE}/api/login/", json=LOGIN_PAYLOAD, status=200)


@rsps_lib.activate
def test_retries_on_500(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", status=500)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", status=500)
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/balance/",
        json={"success": True, "balance": 10.0, "top_up_in_days": 3,
              "pending_top_up": False, "pending_top_up_by": "",
              "last_top_up_time": None, "last_top_up_amount": 0,
              "credit_low": False, "emergency_credit": False,
              "power_off": False, "last_reading": None},
        status=200,
    )
    client = PinergyClient("u@e.com", "p", base_url=BASE, max_retries=2,
                           retry_base_delay=0.001, retry_max_delay=0.01)
    result = client.get_balance()
    assert result.credit_balance == pytest.approx(10.0)
    get_calls = [c for c in rsps_lib.calls if c.request.method == "GET"]
    assert len(get_calls) == 3


@rsps_lib.activate
def test_no_retry_on_post(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.POST, f"{BASE}/api/setnotif/", status=500)
    client = PinergyClient("u@e.com", "p", base_url=BASE, max_retries=2)
    with pytest.raises(PinergyHTTPError):
        client.update_notification_preferences(sms=True, email=True, phone=True)
    post_calls = [c for c in rsps_lib.calls if "/setnotif/" in c.request.url]
    assert len(post_calls) == 1


@rsps_lib.activate
def test_retries_on_connection_error(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET, f"{BASE}/api/balance/",
        body=requests.exceptions.ConnectionError("reset"),
    )
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/balance/",
        json={"success": True, "balance": 5.0, "top_up_in_days": 2,
              "pending_top_up": False, "pending_top_up_by": "",
              "last_top_up_time": None, "last_top_up_amount": 0,
              "credit_low": False, "emergency_credit": False,
              "power_off": False, "last_reading": None},
        status=200,
    )
    client = PinergyClient("u@e.com", "p", base_url=BASE, max_retries=2,
                           retry_base_delay=0.001, retry_max_delay=0.01)
    result = client.get_balance()
    assert result.credit_balance == pytest.approx(5.0)


@rsps_lib.activate
def test_retries_exhausted_raises(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    _add_login(rsps_lib)
    for _ in range(3):
        rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", status=500)
    client = PinergyClient("u@e.com", "p", base_url=BASE, max_retries=2,
                           retry_base_delay=0.001, retry_max_delay=0.01)
    with pytest.raises(PinergyHTTPError):
        client.get_balance()


@rsps_lib.activate
def test_retries_on_timeout(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    _add_login(rsps_lib)
    rsps_lib.add(
        rsps_lib.GET, f"{BASE}/api/balance/",
        body=requests.exceptions.Timeout("timed out"),
    )
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/api/balance/",
        json={"success": True, "balance": 1.0, "top_up_in_days": 1,
              "pending_top_up": False, "pending_top_up_by": "",
              "last_top_up_time": None, "last_top_up_amount": 0,
              "credit_low": False, "emergency_credit": False,
              "power_off": False, "last_reading": None},
        status=200,
    )
    client = PinergyClient("u@e.com", "p", base_url=BASE, max_retries=2,
                           retry_base_delay=0.001, retry_max_delay=0.01)
    result = client.get_balance()
    assert result.credit_balance == pytest.approx(1.0)
