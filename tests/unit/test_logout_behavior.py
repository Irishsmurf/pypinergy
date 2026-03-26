import pytest
import responses
from pypinergy import PinergyClient
from pypinergy.exceptions import PinergyAuthError


@responses.activate
def test_logout_defeats_auto_login():
    responses.add(
        responses.POST,
        "https://api.pinergy.ie/api/login/",
        json={"success": True, "auth_token": "token123"},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://api.pinergy.ie/api/balance/",
        json={"success": True, "balance": 10.0},
        status=200,
    )

    client = PinergyClient("user@example.com", "secret")
    client.login()
    assert client.is_authenticated

    client.logout()
    assert not client.is_authenticated

    # This should fail to login now because password_hash is cleared
    responses.add(
        responses.POST,
        "https://api.pinergy.ie/api/login/",
        json={"success": False, "message": "Login failed"},
        status=200,
    )

    with pytest.raises(PinergyAuthError):
        client.get_balance()
