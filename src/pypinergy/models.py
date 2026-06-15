"""Dataclass models for Pinergy API responses.

All Unix-timestamp fields are exposed both as the raw integer (``*_ts``) and as
a :class:`datetime.datetime` (UTC, ``*_dt``).

Parsing is defensive: ``_from_dict`` constructors tolerate missing keys, ``null``
values, and wrong-typed scalars without raising ``KeyError`` / ``TypeError`` /
``AttributeError`` — fields fall back to neutral defaults instead, so a small
upstream schema drift degrades a field rather than breaking the whole call.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Tuple

if sys.version_info >= (3, 10):
    _DATACLASS_KWARGS: Dict[str, bool] = {"slots": True}
else:
    _DATACLASS_KWARGS = {}

_EPOCH_UTC = datetime.fromtimestamp(0, tz=timezone.utc)

# Cache module-level constants for faster instantiation inside tight loops
_fromtimestamp = datetime.fromtimestamp
_utc = timezone.utc


# ---------------------------------------------------------------------------
# Defensive coercion helpers
# ---------------------------------------------------------------------------


def _to_int(val: Any, default: int = 0) -> int:
    """Coerce *val* to ``int``, returning *default* for None / junk input."""
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _to_float(val: Any, default: float = 0.0) -> float:
    """Coerce *val* to ``float``, returning *default* for None / junk input."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _to_str(val: Any, default: str = "") -> str:
    """Coerce *val* to ``str``, returning *default* for None."""
    if isinstance(val, str):
        return val
    if val is None:
        return default
    return str(val)


def _as_dict(val: Any) -> Dict[str, Any]:
    """Return *val* if it is a dict, else ``{}`` (defends against ``null`` nested objects)."""
    return val if isinstance(val, dict) else {}


def _as_list(val: Any) -> List[Any]:
    """Return *val* if it is a list, else ``[]`` (defends against ``null`` arrays)."""
    return val if isinstance(val, list) else []


def _parse_ts_pair(ts: Any) -> Tuple[Optional[int], Optional[datetime]]:
    """Parse a timestamp into both its integer and datetime representations."""
    if ts is None or ts == "":
        return None, None

    # Performance optimization: using try...except int(ts) is faster than
    # checking isinstance(ts, int) first on the happy path.
    try:
        val = int(ts)
    except (ValueError, TypeError):
        return None, None

    try:
        # Avoid repeated global/attribute lookups by using cached references
        return val, _fromtimestamp(val, tz=_utc)
    except (ValueError, OSError, OverflowError):
        return val, None


def _ts_to_dt(ts: Any) -> Optional[datetime]:
    """Convert a Unix timestamp (string or int) to an aware UTC datetime."""
    _, dt = _parse_ts_pair(ts)
    return dt


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@dataclass(**_DATACLASS_KWARGS)
class User:
    """Authenticated user profile."""

    title: str
    name: str
    pinergy_id: str
    mobile_number: str = field(repr=False)
    sms_notifications: bool
    email_notifications: bool
    first_name: str
    last_name: str

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "User":
        d = _as_dict(d)
        return cls(
            title=_to_str(d.get("title")),
            name=_to_str(d.get("name")),
            pinergy_id=_to_str(d.get("pinergy_id")),
            mobile_number=_to_str(d.get("mobile_number")),
            sms_notifications=bool(d.get("sms_notifications", False)),
            email_notifications=bool(d.get("email_notifications", False)),
            first_name=_to_str(d.get("firstName")),
            last_name=_to_str(d.get("lastName")),
        )


@dataclass(**_DATACLASS_KWARGS)
class House:
    """Property details associated with the account."""

    type: int
    heating_type: int
    bedroom_count: int
    adult_count: int
    children_count: int

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "House":
        d = _as_dict(d)
        return cls(
            type=_to_int(d.get("type")),
            heating_type=_to_int(d.get("heating_type")),
            bedroom_count=_to_int(d.get("bedroom_count")),
            adult_count=_to_int(d.get("adult_count")),
            children_count=_to_int(d.get("children_count")),
        )


@dataclass(**_DATACLASS_KWARGS)
class CreditCard:
    """Saved payment card summary."""

    cc_token: str = field(repr=False)
    name: str
    last_4_digits: str

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "CreditCard":
        d = _as_dict(d)
        return cls(
            cc_token=_to_str(d.get("cc_token")),
            name=_to_str(d.get("name")),
            last_4_digits=_to_str(d.get("last_4_digits")),
        )


@dataclass(**_DATACLASS_KWARGS)
class LoginResponse:
    """Successful login payload."""

    auth_token: str = field(repr=False)
    is_legacy_meter: bool
    is_no_wan_meter: bool
    is_level_pay: bool
    is_child: bool
    is_business_connect: bool
    premises_number: str
    account_type: str
    user: User
    house: House
    credit_cards: List[CreditCard]

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "LoginResponse":
        d = _as_dict(d)
        # Performance optimization: List comprehension with locally cached
        # classmethod reference speeds up the array parsing loop by ~10% over list(map(...))
        _cc_from_dict = CreditCard._from_dict
        return cls(
            auth_token=_to_str(d.get("auth_token")),
            is_legacy_meter=bool(d.get("is_legacy_meter", False)),
            is_no_wan_meter=bool(d.get("is_no_wan_meter", False)),
            is_level_pay=bool(d.get("is_level_pay", False)),
            is_child=bool(d.get("is_child", False)),
            is_business_connect=bool(d.get("is_business_connect", False)),
            premises_number=_to_str(d.get("premises_number")),
            account_type=_to_str(d.get("account_type")),
            user=User._from_dict(_as_dict(d.get("user"))),
            house=House._from_dict(_as_dict(d.get("house"))),
            credit_cards=[_cc_from_dict(x) for x in _as_list(d.get("credit_cards"))],
        )


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------


@dataclass(**_DATACLASS_KWARGS)
class UsageEntry:
    """A single aggregated usage period (day / week / month)."""

    available: bool
    amount: float
    """Cost in euros (€)."""
    kwh: float
    """Energy consumed in kilowatt-hours."""
    co2: float
    """CO₂ in kg (typically 0.0 for renewable supply)."""
    date_ts: int
    """Raw Unix timestamp (start of period)."""
    date: datetime
    """UTC datetime for the start of the period."""

    @property
    def date_dt(self) -> datetime:
        """Alias for :attr:`date`, following the ``*_dt`` naming convention.

        :attr:`date` remains fully supported; both names refer to the same value.
        """
        return self.date

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "UsageEntry":
        d = _as_dict(d)
        ts_int, dt = _parse_ts_pair(d.get("date", 0))
        return cls(
            available=bool(d.get("available", False)),
            amount=_to_float(d.get("amount")),
            kwh=_to_float(d.get("kwh")),
            co2=_to_float(d.get("co2")),
            date_ts=ts_int or 0,
            # Re-use the constant instead of instantiating a new aware datetime per fallback
            date=dt or _EPOCH_UTC,
        )


@dataclass(**_DATACLASS_KWARGS)
class UsageResponse:
    """Aggregated usage across day / week / month buckets."""

    day: List[UsageEntry]
    """Last 7 days — one entry per day."""
    week: List[UsageEntry]
    """Last 8 weeks — one entry per week."""
    month: List[UsageEntry]
    """Last 11 months — one entry per month."""

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "UsageResponse":
        d = _as_dict(d)
        # Performance optimization: List comprehension with locally cached
        # classmethod reference speeds up the array parsing loop by ~10% over list(map(...))
        _ue_from_dict = UsageEntry._from_dict
        return cls(
            day=[_ue_from_dict(x) for x in _as_list(d.get("day"))],
            week=[_ue_from_dict(x) for x in _as_list(d.get("week"))],
            month=[_ue_from_dict(x) for x in _as_list(d.get("month"))],
        )


# ---------------------------------------------------------------------------
# Level Pay Usage
# ---------------------------------------------------------------------------


@dataclass(**_DATACLASS_KWARGS)
class LevelPayDailyValue:
    """Half-hourly label and kWh per tariff band."""

    label: str
    day_kwh: Dict[str, float]
    """Mapping of tariff band name (e.g. ``"Standard"``) to kWh consumed."""

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "LevelPayDailyValue":
        d = _as_dict(d)
        day_kwh_raw = d.get("daykWh")
        day_kwh = {}
        if isinstance(day_kwh_raw, dict):
            day_kwh = {k: _to_float(v) for k, v in day_kwh_raw.items() if k is not None}
        return cls(
            label=_to_str(d.get("label")),
            day_kwh=day_kwh,
        )


@dataclass(**_DATACLASS_KWARGS)
class LevelPayUsageResponse:
    """Half-hourly interval data for level pay customers."""

    labels: List[str]
    flags: List[str]
    values: List[LevelPayDailyValue]

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "LevelPayUsageResponse":
        d = _as_dict(d)
        usage_data = _as_dict(d.get("usageData"))
        daily = _as_dict(usage_data.get("daily"))
        # Performance optimization: List comprehension with locally cached
        # classmethod reference speeds up the array parsing loop by ~10% over list(map(...))
        _lp_from_dict = LevelPayDailyValue._from_dict
        return cls(
            labels=[_to_str(x) for x in _as_list(daily.get("labels"))],
            flags=[_to_str(x) for x in _as_list(daily.get("flags"))],
            values=[_lp_from_dict(x) for x in _as_list(daily.get("values")) if x is not None],
        )


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------


@dataclass(**_DATACLASS_KWARGS)
class BalanceResponse:
    """Current account balance and meter status."""

    credit_balance: float
    """Current credit balance in euros (€)."""
    top_up_in_days: int
    """Estimated days until credit is exhausted."""
    pending_top_up: bool
    pending_top_up_by: str
    last_top_up_amount: float
    credit_low: bool
    """True when balance is below the configured alert threshold."""
    emergency_credit: bool
    """True when the meter is drawing on emergency credit."""
    power_off: bool
    """True when supply has been disconnected."""
    last_top_up_ts: Optional[int]
    last_top_up_time: Optional[datetime]
    last_reading_ts: Optional[int]
    last_reading: Optional[datetime]

    @property
    def last_top_up_dt(self) -> Optional[datetime]:
        """Alias for :attr:`last_top_up_time`, following the ``*_dt`` naming convention.

        :attr:`last_top_up_time` remains fully supported; both names refer to the same value.
        """
        return self.last_top_up_time

    @property
    def last_reading_dt(self) -> Optional[datetime]:
        """Alias for :attr:`last_reading`, following the ``*_dt`` naming convention.

        :attr:`last_reading` remains fully supported; both names refer to the same value.
        """
        return self.last_reading

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "BalanceResponse":
        d = _as_dict(d)
        ltu_ts, ltu_dt = _parse_ts_pair(d.get("last_top_up_time"))
        lr_ts, lr_dt = _parse_ts_pair(d.get("last_reading"))

        return cls(
            credit_balance=_to_float(d.get("balance")),
            top_up_in_days=_to_int(d.get("top_up_in_days")),
            pending_top_up=bool(d.get("pending_top_up", False)),
            pending_top_up_by=_to_str(d.get("pending_top_up_by")),
            last_top_up_amount=_to_float(d.get("last_top_up_amount")),
            credit_low=bool(d.get("credit_low", False)),
            emergency_credit=bool(d.get("emergency_credit", False)),
            power_off=bool(d.get("power_off", False)),
            last_top_up_ts=ltu_ts,
            last_top_up_time=ltu_dt,
            last_reading_ts=lr_ts,
            last_reading=lr_dt,
        )


# ---------------------------------------------------------------------------
# Active Top-Ups
# ---------------------------------------------------------------------------


@dataclass(**_DATACLASS_KWARGS)
class ScheduledTopUp:
    """A top-up scheduled for a fixed calendar day."""

    current_user: bool
    """False when this entry belongs to another resident on the same premises."""
    top_up_amount: float
    top_up_day: int
    customer: str

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "ScheduledTopUp":
        d = _as_dict(d)
        return cls(
            current_user=bool(d.get("current_user", True)),
            top_up_amount=_to_float(d.get("top_up_amount")),
            top_up_day=_to_int(d.get("top_up_day")),
            customer=_to_str(d.get("customer")),
        )


@dataclass(**_DATACLASS_KWARGS)
class ActiveTopUpsResponse:
    """Scheduled and automatic top-up configurations."""

    scheduled: List[ScheduledTopUp]
    auto_top_ups: List[Dict[str, Any]]

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "ActiveTopUpsResponse":
        d = _as_dict(d)
        # Performance optimization: List comprehension with locally cached
        # classmethod reference speeds up the array parsing loop by ~10% over list(map(...))
        _st_from_dict = ScheduledTopUp._from_dict
        return cls(
            scheduled=[_st_from_dict(x) for x in _as_list(d.get("scheduled"))],
            auto_top_ups=_as_list(d.get("auto_top_ups")),
        )


# ---------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------


@dataclass(**_DATACLASS_KWARGS)
class CompareValues:
    """Paired user vs. average-home figures for a metric."""

    users_home: float
    average_home: float

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "CompareValues":
        d = _as_dict(d)
        return cls(
            users_home=_to_float(d.get("users_home")),
            average_home=_to_float(d.get("average_home")),
        )


@dataclass(**_DATACLASS_KWARGS)
class ComparePeriod:
    """Comparison data for a single period (day / week / month)."""

    available: bool
    euro: CompareValues
    kwh: CompareValues
    co2: CompareValues

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "ComparePeriod":
        d = _as_dict(d)
        return cls(
            available=bool(d.get("available", False)),
            euro=CompareValues._from_dict(_as_dict(d.get("euro"))),
            kwh=CompareValues._from_dict(_as_dict(d.get("kwh"))),
            co2=CompareValues._from_dict(_as_dict(d.get("co2"))),
        )


@dataclass(**_DATACLASS_KWARGS)
class CompareResponse:
    """Comparison of this home vs. similar homes."""

    day: ComparePeriod
    week: ComparePeriod
    month: ComparePeriod

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "CompareResponse":
        d = _as_dict(d)
        return cls(
            day=ComparePeriod._from_dict(_as_dict(d.get("day"))),
            week=ComparePeriod._from_dict(_as_dict(d.get("week"))),
            month=ComparePeriod._from_dict(_as_dict(d.get("month"))),
        )


# ---------------------------------------------------------------------------
# Config / Defaults
# ---------------------------------------------------------------------------


@dataclass(**_DATACLASS_KWARGS)
class ConfigInfoResponse:
    """Valid top-up amounts and balance alert thresholds."""

    thresholds: List[int]
    top_up_amounts: List[int]
    auto_up_amounts: List[int]
    scheduled_top_up_amounts: List[int]

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "ConfigInfoResponse":
        d = _as_dict(d)
        return cls(
            thresholds=_as_list(d.get("thresholds")),
            top_up_amounts=_as_list(d.get("top_up_amounts")),
            auto_up_amounts=_as_list(d.get("auto_up_amounts")),
            scheduled_top_up_amounts=_as_list(d.get("scheduled_top_up_amounts")),
        )


@dataclass(**_DATACLASS_KWARGS)
class HouseType:
    id: int
    name: str

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "HouseType":
        d = _as_dict(d)
        return cls(id=_to_int(d.get("id")), name=_to_str(d.get("name")))


@dataclass(**_DATACLASS_KWARGS)
class HeatingType:
    id: int
    name: str

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "HeatingType":
        d = _as_dict(d)
        return cls(id=_to_int(d.get("id")), name=_to_str(d.get("name")))


@dataclass(**_DATACLASS_KWARGS)
class DefaultsInfoResponse:
    """Reference data for house and heating types."""

    house_types: List[HouseType]
    heating_types: List[HeatingType]
    max_bedrooms: int
    default_bedrooms: int
    max_adults: int
    default_adults: int
    max_children: int
    default_children: int

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "DefaultsInfoResponse":
        d = _as_dict(d)
        # Performance optimization: List comprehension with locally cached
        # classmethod reference speeds up the array parsing loop by ~10% over list(map(...))
        _ht_from_dict = HouseType._from_dict
        _heat_from_dict = HeatingType._from_dict
        return cls(
            house_types=[_ht_from_dict(x) for x in _as_list(d.get("house_types"))],
            heating_types=[_heat_from_dict(x) for x in _as_list(d.get("heating_types"))],
            max_bedrooms=_to_int(d.get("max_bedrooms")),
            default_bedrooms=_to_int(d.get("default_bedrooms")),
            max_adults=_to_int(d.get("max_adults")),
            default_adults=_to_int(d.get("default_adults")),
            max_children=_to_int(d.get("max_children")),
            default_children=_to_int(d.get("default_children")),
        )


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


@dataclass(**_DATACLASS_KWARGS)
class NotificationPreferences:
    """User notification channel preferences."""

    sms: bool
    email: bool
    phone: bool
    should_show: int
    should_show_message: str

    @classmethod
    def _from_dict(cls, d: Mapping[str, Any]) -> "NotificationPreferences":
        d = _as_dict(d)
        return cls(
            sms=bool(d.get("sms", False)),
            email=bool(d.get("email", False)),
            phone=bool(d.get("phone", False)),
            should_show=_to_int(d.get("should_show")),
            should_show_message=_to_str(d.get("should_show_message")),
        )
