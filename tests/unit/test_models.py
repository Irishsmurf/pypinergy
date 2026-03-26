"""Unit tests for model parsing."""

from datetime import datetime, timezone

import pytest

from pypinergy.models import (
    ActiveTopUpsResponse,
    BalanceResponse,
    CompareResponse,
    ConfigInfoResponse,
    DefaultsInfoResponse,
    LevelPayUsageResponse,
    LoginResponse,
    NotificationPreferences,
    ScheduledTopUp,
    UsageResponse,
    _ts_to_dt,
    _parse_ts_pair,
)


# ---------------------------------------------------------------------------
# _parse_ts_pair and _ts_to_dt helpers
# ---------------------------------------------------------------------------


def test_parse_ts_pair_valid_int():
    ts, dt = _parse_ts_pair(1773446400)
    assert ts == 1773446400
    assert dt == datetime(2026, 3, 14, tzinfo=timezone.utc)


def test_parse_ts_pair_valid_string():
    ts, dt = _parse_ts_pair("1773446400")
    assert ts == 1773446400
    assert dt == datetime(2026, 3, 14, tzinfo=timezone.utc)


def test_parse_ts_pair_negative():
    ts, dt = _parse_ts_pair("-3600")
    assert ts == -3600
    assert dt == datetime(1969, 12, 31, 23, 0, tzinfo=timezone.utc)


def test_parse_ts_pair_none():
    ts, dt = _parse_ts_pair(None)
    assert ts is None
    assert dt is None


def test_parse_ts_pair_empty_string():
    ts, dt = _parse_ts_pair("")
    assert ts is None
    assert dt is None


def test_parse_ts_pair_invalid_string():
    ts, dt = _parse_ts_pair("not-a-number")
    assert ts is None
    assert dt is None


def test_parse_ts_pair_overflow():
    # Very large number that might cause OverflowError in datetime
    ts, dt = _parse_ts_pair(2**60)
    assert ts == 2**60
    assert dt is None


def test_ts_to_dt_valid_string():
    dt = _ts_to_dt("0")
    assert dt == datetime(1970, 1, 1, tzinfo=timezone.utc)


def test_ts_to_dt_valid_int():
    dt = _ts_to_dt(0)
    assert dt == datetime(1970, 1, 1, tzinfo=timezone.utc)


def test_ts_to_dt_none_returns_none():
    assert _ts_to_dt(None) is None


def test_ts_to_dt_invalid_string_returns_none():
    assert _ts_to_dt("not-a-number") is None


def test_ts_to_dt_result_is_utc():
    dt = _ts_to_dt(1000000)
    assert dt.tzinfo is timezone.utc


# ---------------------------------------------------------------------------
# LoginResponse
# ---------------------------------------------------------------------------


def test_login_response_parsing(conftest_login_payload):
    lr = LoginResponse._from_dict(conftest_login_payload)
    assert lr.auth_token == "TESTTOKEN123"
    assert lr.account_type == "Pinergy Smart"
    assert not lr.is_legacy_meter
    assert not lr.is_level_pay
    assert lr.premises_number == "9372520002113067129"


def test_login_response_user(conftest_login_payload):
    lr = LoginResponse._from_dict(conftest_login_payload)
    assert lr.user.first_name == "Test"
    assert lr.user.last_name == "User"
    assert lr.user.email_notifications is True
    assert lr.user.sms_notifications is False


def test_login_response_house(conftest_login_payload):
    lr = LoginResponse._from_dict(conftest_login_payload)
    assert lr.house.type == 5
    assert lr.house.heating_type == 3
    assert lr.house.bedroom_count == 1


def test_login_response_credit_cards(conftest_login_payload):
    lr = LoginResponse._from_dict(conftest_login_payload)
    assert len(lr.credit_cards) == 1
    card = lr.credit_cards[0]
    assert card.last_4_digits == "5919"
    assert card.name == "Test Card"


# ---------------------------------------------------------------------------
# UsageResponse
# ---------------------------------------------------------------------------


def test_usage_response_parsing(conftest_usage_payload):
    ur = UsageResponse._from_dict(conftest_usage_payload)
    assert len(ur.day) == 2
    assert len(ur.week) == 1
    assert len(ur.month) == 1


def test_usage_entry_fields(conftest_usage_payload):
    entry = UsageResponse._from_dict(conftest_usage_payload).day[0]
    assert entry.available is True
    assert entry.amount == pytest.approx(2.17)
    assert entry.kwh == pytest.approx(2.45)
    assert entry.co2 == pytest.approx(0.0)
    assert entry.date_ts == 1773446400
    assert isinstance(entry.date, datetime)
    assert entry.date.tzinfo is timezone.utc


def test_usage_response_empty_lists():
    ur = UsageResponse._from_dict({"success": True})
    assert ur.day == []
    assert ur.week == []
    assert ur.month == []


# ---------------------------------------------------------------------------
# BalanceResponse
# ---------------------------------------------------------------------------


def test_balance_response_parsing(conftest_balance_payload):
    br = BalanceResponse._from_dict(conftest_balance_payload)
    assert br.credit_balance == pytest.approx(16.38)
    assert br.top_up_in_days == 6
    assert br.pending_top_up is False
    assert br.credit_low is False
    assert br.emergency_credit is False
    assert br.power_off is False
    assert br.last_top_up_amount == pytest.approx(50.0)


def test_balance_response_timestamps(conftest_balance_payload):
    br = BalanceResponse._from_dict(conftest_balance_payload)
    assert br.last_top_up_ts == 1772182668
    assert isinstance(br.last_top_up_time, datetime)
    assert br.last_reading_ts == 1773532800
    assert isinstance(br.last_reading, datetime)


def test_balance_response_missing_timestamps():
    br = BalanceResponse._from_dict({"success": True, "balance": 5.0})
    assert br.last_top_up_ts is None
    assert br.last_top_up_time is None


# ---------------------------------------------------------------------------
# ActiveTopUpsResponse
# ---------------------------------------------------------------------------


def test_active_topups_parsing(conftest_active_topups_payload):
    atr = ActiveTopUpsResponse._from_dict(conftest_active_topups_payload)
    assert len(atr.scheduled) == 1
    assert atr.auto_top_ups == []

    sched = atr.scheduled[0]
    assert isinstance(sched, ScheduledTopUp)
    assert sched.top_up_amount == pytest.approx(150.0)
    assert sched.top_up_day == 13
    assert sched.current_user is False
    assert sched.customer == "PINERGY"


def test_active_topups_empty():
    atr = ActiveTopUpsResponse._from_dict({})
    assert atr.scheduled == []
    assert atr.auto_top_ups == []


# ---------------------------------------------------------------------------
# CompareResponse
# ---------------------------------------------------------------------------


def test_compare_response_parsing(conftest_compare_payload):
    cr = CompareResponse._from_dict(conftest_compare_payload)
    assert cr.day.available is True
    assert cr.day.kwh.users_home == pytest.approx(2.45)
    assert cr.day.kwh.average_home == pytest.approx(8.33)
    assert cr.week.euro.users_home == pytest.approx(17.57)
    assert cr.month.kwh.average_home == pytest.approx(262.66)


def test_compare_period_co2(conftest_compare_payload):
    cr = CompareResponse._from_dict(conftest_compare_payload)
    assert cr.day.co2.users_home == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# ConfigInfoResponse
# ---------------------------------------------------------------------------


def test_config_info_parsing(conftest_config_payload):
    ci = ConfigInfoResponse._from_dict(conftest_config_payload)
    assert ci.thresholds == [5]
    assert 50 in ci.top_up_amounts
    assert 500 in ci.scheduled_top_up_amounts


# ---------------------------------------------------------------------------
# DefaultsInfoResponse
# ---------------------------------------------------------------------------


def test_defaults_info_parsing(conftest_defaults_payload):
    di = DefaultsInfoResponse._from_dict(conftest_defaults_payload)
    assert len(di.house_types) == 3
    assert di.house_types[0].name == "bungalow"
    assert di.heating_types[1].name == "Electricity"
    assert di.max_bedrooms == 6
    assert di.default_bedrooms == 3


# ---------------------------------------------------------------------------
# NotificationPreferences
# ---------------------------------------------------------------------------


def test_notification_preferences_parsing(conftest_notif_payload):
    np = NotificationPreferences._from_dict(conftest_notif_payload)
    assert np.sms is False
    assert np.email is True
    assert np.phone is True
    assert np.should_show == 0


# ---------------------------------------------------------------------------
# LevelPayUsageResponse
# ---------------------------------------------------------------------------


def test_level_pay_usage_parsing(conftest_level_pay_payload):
    lp = LevelPayUsageResponse._from_dict(conftest_level_pay_payload)
    assert lp.labels == ["00:00", "00:30", "01:00"]
    assert lp.flags == ["Standard", "Standard", "Standard"]
    assert len(lp.values) == 1
    assert lp.values[0].label == "14/03"
    assert lp.values[0].day_kwh == {"Standard": 0.5}


# ---------------------------------------------------------------------------
# pytest fixtures (re-expose conftest module-level dicts as fixtures)
# ---------------------------------------------------------------------------


@pytest.fixture
def conftest_login_payload():
    from tests.conftest import LOGIN_PAYLOAD

    return LOGIN_PAYLOAD


@pytest.fixture
def conftest_usage_payload():
    from tests.conftest import USAGE_PAYLOAD

    return USAGE_PAYLOAD


@pytest.fixture
def conftest_balance_payload():
    from tests.conftest import BALANCE_PAYLOAD

    return BALANCE_PAYLOAD


@pytest.fixture
def conftest_active_topups_payload():
    from tests.conftest import ACTIVE_TOPUPS_PAYLOAD

    return ACTIVE_TOPUPS_PAYLOAD


@pytest.fixture
def conftest_compare_payload():
    from tests.conftest import COMPARE_PAYLOAD

    return COMPARE_PAYLOAD


@pytest.fixture
def conftest_config_payload():
    from tests.conftest import CONFIG_PAYLOAD

    return CONFIG_PAYLOAD


@pytest.fixture
def conftest_defaults_payload():
    from tests.conftest import DEFAULTS_PAYLOAD

    return DEFAULTS_PAYLOAD


@pytest.fixture
def conftest_notif_payload():
    from tests.conftest import NOTIF_PAYLOAD

    return NOTIF_PAYLOAD


@pytest.fixture
def conftest_level_pay_payload():
    from tests.conftest import LEVEL_PAY_PAYLOAD

    return LEVEL_PAY_PAYLOAD


# ---------------------------------------------------------------------------
# Sensitve Field __repr__ filtering
# ---------------------------------------------------------------------------

from pypinergy.models import CreditCard, House, User


def test_sensitive_fields_not_in_repr():
    """Verify that sensitive fields are excluded from dataclass __repr__ output."""
    user = User(
        title="Mr",
        name="John Doe",
        pinergy_id="123456",
        mobile_number="0871234567",
        sms_notifications=True,
        email_notifications=True,
        first_name="John",
        last_name="Doe",
    )
    user_repr = repr(user)
    assert "0871234567" not in user_repr
    assert "mobile_number=" not in user_repr
    assert "pinergy_id=" in user_repr

    cc = CreditCard(
        cc_token="secret_stripe_token_5678", name="Visa", last_4_digits="4242"
    )
    cc_repr = repr(cc)
    assert "secret_stripe_token_5678" not in cc_repr
    assert "cc_token=" not in cc_repr
    assert "name=" in cc_repr

    lr = LoginResponse(
        auth_token="super_secret_auth_token_9876",
        is_legacy_meter=False,
        is_no_wan_meter=False,
        is_level_pay=False,
        is_child=False,
        is_business_connect=False,
        premises_number="123",
        account_type="prepay",
        user=user,
        house=House(
            type=0, heating_type=0, bedroom_count=0, adult_count=0, children_count=0
        ),
        credit_cards=[],
    )
    lr_repr = repr(lr)
    assert "super_secret_auth_token_9876" not in lr_repr
    assert "auth_token=" not in lr_repr
    assert "premises_number=" in lr_repr


def test_compare_response_empty():
    cr = CompareResponse._from_dict({})

    assert cr.day.available is False
    assert cr.day.euro.users_home == pytest.approx(0.0)
    assert cr.day.euro.average_home == pytest.approx(0.0)
    assert cr.day.kwh.users_home == pytest.approx(0.0)
    assert cr.day.kwh.average_home == pytest.approx(0.0)
    assert cr.day.co2.users_home == pytest.approx(0.0)
    assert cr.day.co2.average_home == pytest.approx(0.0)

    assert cr.week.available is False
    assert cr.week.euro.users_home == pytest.approx(0.0)
    assert cr.week.euro.average_home == pytest.approx(0.0)
    assert cr.week.kwh.users_home == pytest.approx(0.0)
    assert cr.week.kwh.average_home == pytest.approx(0.0)
    assert cr.week.co2.users_home == pytest.approx(0.0)
    assert cr.week.co2.average_home == pytest.approx(0.0)

    assert cr.month.available is False
    assert cr.month.euro.users_home == pytest.approx(0.0)
    assert cr.month.euro.average_home == pytest.approx(0.0)
    assert cr.month.kwh.users_home == pytest.approx(0.0)
    assert cr.month.kwh.average_home == pytest.approx(0.0)
    assert cr.month.co2.users_home == pytest.approx(0.0)
    assert cr.month.co2.average_home == pytest.approx(0.0)
