"""Shared pytest fixtures."""

import pytest

# ---------------------------------------------------------------------------
# Fixture payloads — mirror real API responses
# ---------------------------------------------------------------------------

LOGIN_PAYLOAD = {
    "success": True,
    "error_code": 0,
    "message": None,
    "auth_token": "TESTTOKEN123",
    "is_legacy_meter": False,
    "is_no_wan_meter": False,
    "is_level_pay": False,
    "is_child": False,
    "is_business_connect": False,
    "premises_number": "9372520002113067129",
    "account_type": "Pinergy Smart",
    "user": {
        "title": "Mr.",
        "name": "Test User",
        "pinergy_id": "eca738f0-042e-4ec8-ac5e-6813ee5bf4b3",
        "mobile_number": "353871234567",
        "sms_notifications": False,
        "email_notifications": True,
        "firstName": "Test",
        "lastName": "User",
    },
    "house": {
        "type": 5,
        "heating_type": 3,
        "bedroom_count": 1,
        "adult_count": 1,
        "children_count": 0,
    },
    "credit_cards": [
        {
            "cc_token": "X0ZZ63cdb6fe628de83DVW5QXF4OEFG5",
            "name": "Test Card",
            "last_4_digits": "5919",
        }
    ],
    "usageData": None,
}

USAGE_PAYLOAD = {
    "success": True,
    "day": [
        {"available": True, "amount": 2.17, "kwh": 2.45, "co2": 0.0, "date": "1773446400"},
        {"available": True, "amount": 1.80, "kwh": 2.10, "co2": 0.0, "date": "1773360000"},
    ],
    "week": [
        {"available": True, "amount": 14.67, "kwh": 19.1, "co2": 0.0, "date": "1773014400"},
    ],
    "month": [
        {"available": True, "amount": 80.41, "kwh": 121.6, "co2": 0.0, "date": "1769904000"},
    ],
}

BALANCE_PAYLOAD = {
    "success": True,
    "balance": 16.38,
    "top_up_in_days": 6,
    "pending_top_up": False,
    "pending_top_up_by": "",
    "last_top_up_time": "1772182668",
    "last_top_up_amount": 50.0,
    "credit_low": False,
    "emergency_credit": False,
    "power_off": False,
    "last_reading": "1773532800",
}

ACTIVE_TOPUPS_PAYLOAD = {
    "success": True,
    "scheduled": [
        {
            "current_user": False,
            "top_up_amount": 150.0,
            "top_up_day": 13,
            "customer": "PINERGY",
        }
    ],
    "auto_top_ups": [],
}

COMPARE_PAYLOAD = {
    "success": True,
    "day": {
        "available": True,
        "euro": {"users_home": 2.17, "average_home": 2.48},
        "kwh": {"users_home": 2.45, "average_home": 8.33},
        "co2": {"users_home": 0.0, "average_home": 0.0},
    },
    "week": {
        "available": True,
        "euro": {"users_home": 17.57, "average_home": 17.37},
        "kwh": {"users_home": 23.5, "average_home": 58.32},
        "co2": {"users_home": 0.0, "average_home": 0.0},
    },
    "month": {
        "available": True,
        "euro": {"users_home": 80.41, "average_home": 75.81},
        "kwh": {"users_home": 121.6, "average_home": 262.66},
        "co2": {"users_home": 0.0, "average_home": 0.0},
    },
}

CONFIG_PAYLOAD = {
    "success": True,
    "thresholds": [5],
    "top_up_amounts": [10, 15, 20, 25, 30, 40, 50, 100, 150, 200, 500],
    "auto_up_amounts": [10, 15, 20, 25, 30, 40, 50, 100, 150, 200, 500],
    "scheduled_top_up_amounts": [10, 15, 20, 25, 30, 40, 50, 100, 150, 200, 500],
}

DEFAULTS_PAYLOAD = {
    "success": True,
    "house_types": [
        {"id": 1, "name": "bungalow"},
        {"id": 2, "name": "semi-detached"},
        {"id": 5, "name": "apartment"},
    ],
    "heating_types": [
        {"id": 1, "name": "Oil"},
        {"id": 3, "name": "Electricity"},
    ],
    "max_bedrooms": 6,
    "default_bedrooms": 3,
    "max_adults": 6,
    "default_adults": 0,
    "max_children": 6,
    "default_children": 0,
}

NOTIF_PAYLOAD = {
    "success": True,
    "sms": False,
    "email": True,
    "phone": True,
    "should_show": 0,
    "should_show_message": "",
}

LEVEL_PAY_PAYLOAD = {
    "usageData": {
        "daily": {
            "labels": ["00:00", "00:30", "01:00"],
            "flags": ["Standard", "Standard", "Standard"],
            "values": [
                {"label": "14/03", "daykWh": {"Standard": 0.5}},
            ],
        }
    }
}
