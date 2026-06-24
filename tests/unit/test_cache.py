"""Unit tests for in-memory TTL response caching (#198)."""

import time

import responses as rsps_lib

from pypinergy import PinergyClient
from pypinergy.client import _TTLCache
from tests.conftest import BALANCE_PAYLOAD, LOGIN_PAYLOAD

BASE = "https://api.pinergy.ie"


def _add_login(rsps):
    rsps.add(rsps_lib.POST, f"{BASE}/api/login/", json=LOGIN_PAYLOAD, status=200)


class TestTTLCache:
    def test_put_and_get(self):
        cache = _TTLCache({"/a": 10.0})
        cache.put("/a", b'{"x":1}')
        assert cache.get("/a") == b'{"x":1}'

    def test_get_missing_key(self):
        cache = _TTLCache({"/a": 10.0})
        assert cache.get("/a") is None

    def test_expired_entry_returns_none(self):
        cache = _TTLCache({"/a": 0.001})
        cache.put("/a", b'{"x":1}')
        time.sleep(0.01)
        assert cache.get("/a") is None

    def test_no_ttl_skips_cache(self):
        cache = _TTLCache({})
        cache.put("/a", b'{"x":1}')
        assert cache.get("/a") is None

    def test_oversized_entry_skipped(self):
        cache = _TTLCache({"/a": 10.0})
        cache.put("/a", b"x" * (_TTLCache._MAX_ENTRY_SIZE + 1))
        assert cache.get("/a") is None

    def test_flush(self):
        cache = _TTLCache({"/a": 10.0, "/b": 10.0})
        cache.put("/a", b"1")
        cache.put("/b", b"2")
        cache.flush()
        assert cache.get("/a") is None
        assert cache.get("/b") is None

    def test_invalidate(self):
        cache = _TTLCache({"/a": 10.0, "/b": 10.0})
        cache.put("/a", b"1")
        cache.put("/b", b"2")
        cache.invalidate("/a")
        assert cache.get("/a") is None
        assert cache.get("/b") == b"2"


@rsps_lib.activate
def test_cached_response_avoids_second_request():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", json=BALANCE_PAYLOAD, status=200)
    client = PinergyClient("u@e.com", "p", base_url=BASE)
    client.get_balance()
    client.get_balance()
    get_calls = [c for c in rsps_lib.calls if c.request.method == "GET"]
    assert len(get_calls) == 1


@rsps_lib.activate
def test_cache_disabled():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", json=BALANCE_PAYLOAD, status=200)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", json=BALANCE_PAYLOAD, status=200)
    client = PinergyClient("u@e.com", "p", base_url=BASE, cache_disabled=True)
    client.get_balance()
    client.get_balance()
    get_calls = [c for c in rsps_lib.calls if c.request.method == "GET"]
    assert len(get_calls) == 2


@rsps_lib.activate
def test_logout_flushes_cache():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", json=BALANCE_PAYLOAD, status=200)
    client = PinergyClient("u@e.com", "p", base_url=BASE)
    client.get_balance()
    client.logout()
    assert client._cache.get("/api/balance/") is None


@rsps_lib.activate
def test_cache_flush_method():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", json=BALANCE_PAYLOAD, status=200)
    client = PinergyClient("u@e.com", "p", base_url=BASE)
    client.get_balance()
    client.cache_flush()
    assert client._cache.get("/api/balance/") is None


@rsps_lib.activate
def test_cache_invalidate_method():
    _add_login(rsps_lib)
    rsps_lib.add(rsps_lib.GET, f"{BASE}/api/balance/", json=BALANCE_PAYLOAD, status=200)
    client = PinergyClient("u@e.com", "p", base_url=BASE)
    client.get_balance()
    client.cache_invalidate("/api/balance/")
    assert client._cache.get("/api/balance/") is None
