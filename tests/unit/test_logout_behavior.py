import pytest
import responses
from pypinergy import PinergyClient
from pypinergy.exceptions import PinergyAuthError

@responses.activate
def test_logout_defeats_auto_login():
    responses.add(
        responses.POST,
        "https://api.pinergy.ie/api/login/",
        json={"success": True, "auth_token": "token123", "is_legacy_meter": False, "is_no_wan_meter": False, "is_level_pay": False, "is_child": False, "is_business_connect": False, "premises_number": "1", "account_type": "1", "user": {}, "house": {}, "credit_cards": []},
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
