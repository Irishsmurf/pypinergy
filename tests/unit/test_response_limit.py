"""Unit tests for response body size limit (#199)."""

import pytest
import responses as rsps_lib

from pypinergy import PinergyClient
from pypinergy.exceptions import PinergyResponseError

BASE = "https://api.pinergy.ie"


@rsps_lib.activate
def test_response_exceeding_limit_raises_error():
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/version.json",
        body=b"x" * 200,
        status=200,
    )
    client = PinergyClient("u@e.com", "p", base_url=BASE, max_response_bytes=100)
    with pytest.raises(PinergyResponseError, match="exceeds limit"):
        client.get_version()


@rsps_lib.activate
def test_response_within_limit_succeeds():
    rsps_lib.add(
        rsps_lib.GET,
        f"{BASE}/version.json",
        json={"ok": True},
        status=200,
    )
    client = PinergyClient("u@e.com", "p", base_url=BASE, max_response_bytes=10_000)
    result = client.get_version()
    assert result["ok"] is True
