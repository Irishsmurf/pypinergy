# pypinergy

[![CI](https://github.com/irishsmurf/pypinergy/actions/workflows/ci.yml/badge.svg)](https://github.com/irishsmurf/pypinergy/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/irishsmurf/pypinergy/graph/badge.svg)](https://codecov.io/gh/irishsmurf/pypinergy)
[![PyPI](https://img.shields.io/pypi/v/pypinergy)](https://pypi.org/project/pypinergy/)
[![Python](https://img.shields.io/pypi/pyversions/pypinergy)](https://pypi.org/project/pypinergy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python client library for the [Pinergy](https://www.pinergy.ie) smart-meter API.

> **Note:** This library is built on a reverse-engineered, unofficial API.
> It is not affiliated with or endorsed by Pinergy.

---

## Installation

```bash
pip install pypinergy
```

Requires **Python 3.9+** and [`requests`](https://requests.readthedocs.io/).

---

## Quick Start

```python
from pypinergy import PinergyClient

client = PinergyClient("you@example.com", "your-password")

# Check your current balance
balance = client.get_balance()
print(f"Balance: €{balance.credit_balance:.2f}")
print(f"Estimated days remaining: {balance.top_up_in_days}")

# Today's usage
usage = client.get_usage()
today = usage.day[0]
print(f"{today.date:%Y-%m-%d}  {today.kwh:.2f} kWh  €{today.amount:.2f}")
```

Authentication is **lazy** — the client logs in automatically on the first API
call. You can also call `.login()` explicitly if you want the `LoginResponse`
data (account details, credit cards, etc.).

---

## Authentication

### Automatic (recommended)

```python
client = PinergyClient("you@example.com", "your-password")
# First API call triggers login transparently
balance = client.get_balance()
```

### Explicit login

```python
from pypinergy import PinergyClient

client = PinergyClient("you@example.com", "your-password")
login = client.login()

print(f"Welcome, {login.user.first_name}!")
print(f"Account type: {login.account_type}")
print(f"Premises: {login.premises_number}")
print(f"Level pay: {login.is_level_pay}")
```

### Check if an email is registered

```python
if client.check_email("someone@example.com"):
    print("Account exists")
else:
    print("No account found for that email")
```

### Logout

```python
client.logout()
print(client.is_authenticated)  # False
```

---

## Usage Data

### Smart / PAYG customers

```python
usage = client.get_usage()

print("--- Daily (last 7 days) ---")
for entry in usage.day:
    print(f"  {entry.date:%Y-%m-%d}  {entry.kwh:6.2f} kWh  €{entry.amount:.2f}")

print("--- Weekly (last 8 weeks) ---")
for entry in usage.week:
    print(f"  w/c {entry.date:%Y-%m-%d}  {entry.kwh:7.2f} kWh  €{entry.amount:.2f}")

print("--- Monthly (last 11 months) ---")
for entry in usage.month:
    print(f"  {entry.date:%Y-%m}  {entry.kwh:8.2f} kWh  €{entry.amount:.2f}")
```

Each `UsageEntry` has:

| Field | Type | Description |
|---|---|---|
| `available` | `bool` | Whether data is available for this period |
| `amount` | `float` | Cost in euros (€) |
| `kwh` | `float` | Energy consumed in kilowatt-hours |
| `co2` | `float` | CO₂ in kg (0.0 for renewable supply) |
| `date` | `datetime` | UTC datetime for the start of the period |
| `date_ts` | `int` | Raw Unix timestamp |

### Level Pay customers

```python
lp = client.get_level_pay_usage()

print("Half-hourly labels:", lp.labels[:4])   # ["00:00", "00:30", ...]
print("Tariff flags:", lp.flags[:2])           # ["Standard", ...]
for day_val in lp.values:
    print(f"  {day_val.label}: {day_val.day_kwh}")
```

---

## Balance

```python
bal = client.get_balance()

print(f"Current balance:    €{bal.credit_balance:.2f}")
print(f"Days remaining:     {bal.top_up_in_days}")
print(f"Last top-up:        €{bal.last_top_up_amount:.2f} on {bal.last_top_up_time:%Y-%m-%d}")
print(f"Last meter reading: {bal.last_reading:%Y-%m-%d %H:%M UTC}")
print(f"Credit low?         {bal.credit_low}")
print(f"Emergency credit?   {bal.emergency_credit}")
print(f"Power off?          {bal.power_off}")
```

`BalanceResponse` fields:

| Field | Type | Description |
|---|---|---|
| `credit_balance` | `float` | Credit balance in euros (€) |
| `top_up_in_days` | `int` | Estimated days until credit runs out |
| `pending_top_up` | `bool` | Whether a top-up is pending |
| `pending_top_up_by` | `str` | Who initiated the pending top-up |
| `last_top_up_amount` | `float` | Amount of last top-up (€) |
| `last_top_up_time` | `datetime \| None` | UTC datetime of last top-up |
| `last_top_up_ts` | `int \| None` | Raw Unix timestamp of last top-up |
| `last_reading` | `datetime \| None` | UTC datetime of last meter reading |
| `last_reading_ts` | `int \| None` | Raw Unix timestamp of last reading |
| `credit_low` | `bool` | Balance below configured threshold |
| `emergency_credit` | `bool` | On emergency credit |
| `power_off` | `bool` | Supply disconnected |

---

## Top-Ups

```python
topups = client.get_active_topups()

for sched in topups.scheduled:
    owner = "you" if sched.current_user else sched.customer
    print(f"  Day {sched.top_up_day:2d} of each month: €{sched.top_up_amount:.0f}  ({owner})")

if topups.auto_top_ups:
    print("Auto top-ups configured:", topups.auto_top_ups)
```

> `current_user: False` means the scheduled top-up belongs to another resident
> on the same premises (e.g. in an apartment building).

---

## Usage Comparison

Compare your home's usage against a cohort of similar homes:

```python
cmp = client.compare_usage()

for label, period in [("Today", cmp.day), ("This week", cmp.week), ("This month", cmp.month)]:
    if not period.available:
        continue
    diff_kwh = period.kwh.users_home - period.kwh.average_home
    direction = "more" if diff_kwh > 0 else "less"
    print(
        f"{label}: {period.kwh.users_home:.1f} kWh "
        f"({abs(diff_kwh):.1f} kWh {direction} than average)"
    )
```

`ComparePeriod` has three metric groups — `euro`, `kwh`, `co2` — each with
`users_home` and `average_home` floats.

---

## Configuration

### Valid top-up amounts and alert thresholds

```python
cfg = client.get_config_info()
print("Top-up options:", cfg.top_up_amounts)
print("Low-balance thresholds:", cfg.thresholds)
```

### House and heating type reference data

```python
defaults = client.get_defaults_info()
for ht in defaults.house_types:
    print(f"  {ht.id}: {ht.name}")
for ht in defaults.heating_types:
    print(f"  {ht.id}: {ht.name}")
```

---

## Notifications

```python
notif = client.get_notification_preferences()
print(f"Email notifications: {notif.email}")
print(f"SMS notifications:   {notif.sms}")
print(f"Phone notifications: {notif.phone}")
```

---

## Device Token (FCM)

For headless / server-side usage you can pass an empty string or skip this
entirely — it only affects push notifications on mobile devices.

```python
client.update_device_token(
    device_token="",      # empty for headless use
    device_type="android",
    os_version="",
)
```

---

## App Version

Unauthenticated endpoint — does not require a login:

```python
version_info = client.get_version()
print(version_info)
```

---

## Error Handling

```python
from pypinergy import PinergyClient
from pypinergy.exceptions import PinergyAuthError, PinergyAPIError, PinergyHTTPError

client = PinergyClient("you@example.com", "wrong-password")

try:
    client.login()
except PinergyAuthError as e:
    print(f"Bad credentials: {e}")

try:
    balance = client.get_balance()
except PinergyAPIError as e:
    print(f"API error {e.error_code}: {e.message}")
except PinergyHTTPError as e:
    print(f"Network error: {e}")
```

| Exception | When raised |
|---|---|
| `PinergyError` | Base class for all library errors |
| `PinergyAuthError` | Invalid credentials or expired session |
| `PinergyAPIError` | API returned `success: false` (has `.error_code` and `.message`) |
| `PinergyHTTPError` | Network-level failure (timeout, 5xx, DNS, etc.) |

---

## Advanced Usage

### Custom timeout

```python
client = PinergyClient("you@example.com", "password", timeout=10)
```

### Custom base URL (testing / proxy)

```python
client = PinergyClient("you@example.com", "password", base_url="http://localhost:8080")
```

### Checking account type before fetching usage

```python
login = client.login()

if login.is_level_pay:
    data = client.get_level_pay_usage()
else:
    data = client.get_usage()
```

---

## Running Tests

### Unit tests (no credentials required)

```bash
pip install -e ".[dev]"
pytest tests/unit/ -v
```

### Integration tests (real API)

```bash
export PINERGY_EMAIL=you@example.com
export PINERGY_PASSWORD=your-password
pytest tests/integration/ -v
```

### All tests with coverage

```bash
pytest --cov=pypinergy --cov-report=html
```

---

## Publishing to PyPI

```bash
pip install build twine

# Build distribution
python -m build

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

Or use [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) via
GitHub Actions — add a `.github/workflows/publish.yml` that triggers on a
version tag.

---

## License

MIT
