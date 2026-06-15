"""pypinergy — Python client for the Pinergy smart-meter API."""

from .client import PinergyClient
from .exceptions import (
    PinergyAPIError,
    PinergyAuthError,
    PinergyError,
    PinergyHTTPError,
    PinergyResponseError,
    PinergyTimeoutError,
)
from .models import (
    ActiveTopUpsResponse,
    BalanceResponse,
    ComparePeriod,
    CompareResponse,
    CompareValues,
    ConfigInfoResponse,
    CreditCard,
    DefaultsInfoResponse,
    HeatingType,
    House,
    HouseType,
    LevelPayDailyValue,
    LevelPayUsageResponse,
    LoginResponse,
    NotificationPreferences,
    ScheduledTopUp,
    TopUpResponse,
    UsageEntry,
    UsageResponse,
    User,
)

__all__ = [
    # Client
    "PinergyClient",
    # Exceptions
    "PinergyError",
    "PinergyAPIError",
    "PinergyAuthError",
    "PinergyHTTPError",
    "PinergyResponseError",
    "PinergyTimeoutError",
    # Models
    "LoginResponse",
    "User",
    "House",
    "CreditCard",
    "UsageResponse",
    "UsageEntry",
    "LevelPayUsageResponse",
    "LevelPayDailyValue",
    "BalanceResponse",
    "ActiveTopUpsResponse",
    "ScheduledTopUp",
    "TopUpResponse",
    "CompareResponse",
    "ComparePeriod",
    "CompareValues",
    "ConfigInfoResponse",
    "DefaultsInfoResponse",
    "HouseType",
    "HeatingType",
    "NotificationPreferences",
]

__version__ = "1.0.0"
