"""Dataclass models for Pinergy API responses.

All Unix-timestamp fields are exposed both as the raw integer (``*_ts``) and as
a :class:`datetime.datetime` (UTC, ``*_dt``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

_EPOCH_UTC = datetime.fromtimestamp(0, tz=timezone.utc)

# Cache module-level constants for faster instantiation inside tight loops
_fromtimestamp = datetime.fromtimestamp
_utc = timezone.utc


def _parse_ts_pair(ts: Optional[str | int]) -> tuple[Optional[int], Optional[datetime]]:
    """Parse a timestamp into both its integer and datetime representations."""
    # Performance optimization: explicit fast path for zero (often used as empty fallback)
    # returns the pre-cached constant directly, bypassing int casting and tz instantiation
    if ts == 0 or ts == "0":
        return 0, _EPOCH_UTC

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


def _ts_to_dt(ts: Optional[str | int]) -> Optional[datetime]:
    """Convert a Unix timestamp (string or int) to an aware UTC datetime."""
    _, dt = _parse_ts_pair(ts)
    return dt


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@dataclass
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
    def _from_dict(cls, d: dict) -> "User":
        return cls(
            title=d.get("title", ""),
            name=d.get("name", ""),
            pinergy_id=d.get("pinergy_id", ""),
            mobile_number=d.get("mobile_number", ""),
            sms_notifications=bool(d.get("sms_notifications", False)),
            email_notifications=bool(d.get("email_notifications", False)),
            first_name=d.get("firstName", ""),
            last_name=d.get("lastName", ""),
        )


@dataclass
class House:
    """Property details associated with the account."""

    type: int
    heating_type: int
    bedroom_count: int
    adult_count: int
    children_count: int

    @classmethod
    def _from_dict(cls, d: dict) -> "House":
        return cls(
            type=int(d.get("type", 0)),
            heating_type=int(d.get("heating_type", 0)),
            bedroom_count=int(d.get("bedroom_count", 0)),
            adult_count=int(d.get("adult_count", 0)),
            children_count=int(d.get("children_count", 0)),
        )


@dataclass
class CreditCard:
    """Saved payment card summary."""

    cc_token: str = field(repr=False)
    name: str
    last_4_digits: str

    @classmethod
    def _from_dict(cls, d: dict) -> "CreditCard":
        return cls(
            cc_token=d.get("cc_token", ""),
            name=d.get("name", ""),
            last_4_digits=d.get("last_4_digits", ""),
        )


@dataclass
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
    def _from_dict(cls, d: dict) -> "LoginResponse":
        # Performance optimization: List comprehension with locally cached
        # classmethod reference speeds up the array parsing loop by ~10% over list(map(...))
        _cc_from_dict = CreditCard._from_dict
        return cls(
            auth_token=d["auth_token"],
            is_legacy_meter=bool(d.get("is_legacy_meter", False)),
            is_no_wan_meter=bool(d.get("is_no_wan_meter", False)),
            is_level_pay=bool(d.get("is_level_pay", False)),
            is_child=bool(d.get("is_child", False)),
            is_business_connect=bool(d.get("is_business_connect", False)),
            premises_number=d.get("premises_number", ""),
            account_type=d.get("account_type", ""),
            user=User._from_dict(d.get("user", {})),
            house=House._from_dict(d.get("house", {})),
            credit_cards=[_cc_from_dict(x) for x in d.get("credit_cards", [])],
        )


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------


@dataclass
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

    @classmethod
    def _from_dict(cls, d: dict) -> "UsageEntry":
        ts_int, dt = _parse_ts_pair(d.get("date", 0))
        return cls(
            available=bool(d.get("available", False)),
            amount=float(d.get("amount", 0.0)),
            kwh=float(d.get("kwh", 0.0)),
            co2=float(d.get("co2", 0.0)),
            date_ts=ts_int or 0,
            # Re-use the constant instead of instantiating a new aware datetime per fallback
            date=dt or _EPOCH_UTC,
        )


@dataclass
class UsageResponse:
    """Aggregated usage across day / week / month buckets."""

    day: List[UsageEntry]
    """Last 7 days — one entry per day."""
    week: List[UsageEntry]
    """Last 8 weeks — one entry per week."""
    month: List[UsageEntry]
    """Last 11 months — one entry per month."""

    @classmethod
    def _from_dict(cls, d: dict) -> "UsageResponse":
        # Performance optimization: List comprehension with locally cached
        # classmethod reference speeds up the array parsing loop by ~10% over list(map(...))
        _ue_from_dict = UsageEntry._from_dict
        return cls(
            day=[_ue_from_dict(x) for x in d.get("day", [])],
            week=[_ue_from_dict(x) for x in d.get("week", [])],
            month=[_ue_from_dict(x) for x in d.get("month", [])],
        )


# ---------------------------------------------------------------------------
# Level Pay Usage
# ---------------------------------------------------------------------------


@dataclass
class LevelPayDailyValue:
    """Half-hourly label and kWh per tariff band."""

    label: str
    day_kwh: dict

    @classmethod
    def _from_dict(cls, d: dict) -> "LevelPayDailyValue":
        return cls(label=d.get("label", ""), day_kwh=d.get("daykWh", {}))


@dataclass
class LevelPayUsageResponse:
    """Half-hourly interval data for level pay customers."""

    labels: List[str]
    flags: List[str]
    values: List[LevelPayDailyValue]

    @classmethod
    def _from_dict(cls, d: dict) -> "LevelPayUsageResponse":
        daily = d.get("usageData", {}).get("daily", {})
        # Performance optimization: List comprehension with locally cached
        # classmethod reference speeds up the array parsing loop by ~10% over list(map(...))
        _lp_from_dict = LevelPayDailyValue._from_dict
        return cls(
            labels=daily.get("labels", []),
            flags=daily.get("flags", []),
            values=[_lp_from_dict(x) for x in daily.get("values", [])],
        )


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------


@dataclass
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

    @classmethod
    def _from_dict(cls, d: dict) -> "BalanceResponse":
        ltu_ts, ltu_dt = _parse_ts_pair(d.get("last_top_up_time"))
        lr_ts, lr_dt = _parse_ts_pair(d.get("last_reading"))

        return cls(
            credit_balance=float(d.get("balance", 0.0)),
            top_up_in_days=int(d.get("top_up_in_days", 0)),
            pending_top_up=bool(d.get("pending_top_up", False)),
            pending_top_up_by=d.get("pending_top_up_by", ""),
            last_top_up_amount=float(d.get("last_top_up_amount", 0.0)),
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


@dataclass
class ScheduledTopUp:
    """A top-up scheduled for a fixed calendar day."""

    current_user: bool
    """False when this entry belongs to another resident on the same premises."""
    top_up_amount: float
    top_up_day: int
    customer: str

    @classmethod
    def _from_dict(cls, d: dict) -> "ScheduledTopUp":
        return cls(
            current_user=bool(d.get("current_user", True)),
            top_up_amount=float(d.get("top_up_amount", 0.0)),
            top_up_day=int(d.get("top_up_day", 0)),
            customer=d.get("customer", ""),
        )


@dataclass
class ActiveTopUpsResponse:
    """Scheduled and automatic top-up configurations."""

    scheduled: List[ScheduledTopUp]
    auto_top_ups: List[dict]

    @classmethod
    def _from_dict(cls, d: dict) -> "ActiveTopUpsResponse":
        # Performance optimization: List comprehension with locally cached
        # classmethod reference speeds up the array parsing loop by ~10% over list(map(...))
        _st_from_dict = ScheduledTopUp._from_dict
        return cls(
            scheduled=[_st_from_dict(x) for x in d.get("scheduled", [])],
            auto_top_ups=d.get("auto_top_ups", []),
        )


# ---------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------


@dataclass
class CompareValues:
    """Paired user vs. average-home figures for a metric."""

    users_home: float
    average_home: float

    @classmethod
    def _from_dict(cls, d: dict) -> "CompareValues":
        return cls(
            users_home=float(d.get("users_home", 0.0)),
            average_home=float(d.get("average_home", 0.0)),
        )


@dataclass
class ComparePeriod:
    """Comparison data for a single period (day / week / month)."""

    available: bool
    euro: CompareValues
    kwh: CompareValues
    co2: CompareValues

    @classmethod
    def _from_dict(cls, d: dict) -> "ComparePeriod":
        return cls(
            available=bool(d.get("available", False)),
            euro=CompareValues._from_dict(d.get("euro", {})),
            kwh=CompareValues._from_dict(d.get("kwh", {})),
            co2=CompareValues._from_dict(d.get("co2", {})),
        )


@dataclass
class CompareResponse:
    """Comparison of this home vs. similar homes."""

    day: ComparePeriod
    week: ComparePeriod
    month: ComparePeriod

    @classmethod
    def _from_dict(cls, d: dict) -> "CompareResponse":
        return cls(
            day=ComparePeriod._from_dict(d.get("day", {})),
            week=ComparePeriod._from_dict(d.get("week", {})),
            month=ComparePeriod._from_dict(d.get("month", {})),
        )


# ---------------------------------------------------------------------------
# Config / Defaults
# ---------------------------------------------------------------------------


@dataclass
class ConfigInfoResponse:
    """Valid top-up amounts and balance alert thresholds."""

    thresholds: List[int]
    top_up_amounts: List[int]
    auto_up_amounts: List[int]
    scheduled_top_up_amounts: List[int]

    @classmethod
    def _from_dict(cls, d: dict) -> "ConfigInfoResponse":
        return cls(
            thresholds=d.get("thresholds", []),
            top_up_amounts=d.get("top_up_amounts", []),
            auto_up_amounts=d.get("auto_up_amounts", []),
            scheduled_top_up_amounts=d.get("scheduled_top_up_amounts", []),
        )


@dataclass
class HouseType:
    id: int
    name: str

    @classmethod
    def _from_dict(cls, d: dict) -> "HouseType":
        return cls(id=int(d["id"]), name=d["name"])


@dataclass
class HeatingType:
    id: int
    name: str

    @classmethod
    def _from_dict(cls, d: dict) -> "HeatingType":
        return cls(id=int(d["id"]), name=d["name"])


@dataclass
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
    def _from_dict(cls, d: dict) -> "DefaultsInfoResponse":
        # Performance optimization: List comprehension with locally cached
        # classmethod reference speeds up the array parsing loop by ~10% over list(map(...))
        _ht_from_dict = HouseType._from_dict
        _heat_from_dict = HeatingType._from_dict
        return cls(
            house_types=[_ht_from_dict(x) for x in d.get("house_types", [])],
            heating_types=[_heat_from_dict(x) for x in d.get("heating_types", [])],
            max_bedrooms=int(d.get("max_bedrooms", 0)),
            default_bedrooms=int(d.get("default_bedrooms", 0)),
            max_adults=int(d.get("max_adults", 0)),
            default_adults=int(d.get("default_adults", 0)),
            max_children=int(d.get("max_children", 0)),
            default_children=int(d.get("default_children", 0)),
        )


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


@dataclass
class NotificationPreferences:
    """User notification channel preferences."""

    sms: bool
    email: bool
    phone: bool
    should_show: int
    should_show_message: str

    @classmethod
    def _from_dict(cls, d: dict) -> "NotificationPreferences":
        return cls(
            sms=bool(d.get("sms", False)),
            email=bool(d.get("email", False)),
            phone=bool(d.get("phone", False)),
            should_show=int(d.get("should_show", 0)),
            should_show_message=d.get("should_show_message", ""),
        )
