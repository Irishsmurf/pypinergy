# User Guide

This guide provides a comprehensive overview of how to use **PyPinergy** to interact with your Pinergy smart-meter data.

## Installation

PyPinergy requires **Python 3.9+** and the `requests` library.

```bash
pip install pypinergy
```

## Getting Started

The primary entry point is the `PinergyClient` class. It manages authentication and connection pooling.

### Context Manager (Recommended)

Using the client as a context manager ensures that the underlying HTTP connection pool is closed deterministically when you're done.

```python
from pypinergy import PinergyClient

with PinergyClient("you@example.com", "your-password") as client:
    balance = client.get_balance()
    print(f"Balance: €{balance.credit_balance:.2f}")
```

### Manual Lifecycle Management

If you can't use a context manager, remember to call `.close()` to release resources.

```python
client = PinergyClient("you@example.com", "your-password")
try:
    balance = client.get_balance()
finally:
    client.close()
```

---

## Authentication

PyPinergy implements **lazy authentication**. You don't need to call `.login()` explicitly; the client will authenticate automatically on the first API call that requires it.

### Thread Safety

Lazy login is thread-safe. If multiple threads make their first API call simultaneously, they will wait for a single shared login operation to complete.

### Explicit Login

If you need the detailed account information returned upon login (such as premises number or saved credit cards), you can call `.login()` manually.

```python
login = client.login()
print(f"Account: {login.premises_number}")
for card in login.credit_cards:
    print(f"Card ending in {card.last_4_digits}")
```

### Logout

Calling `.logout()` clears the stored authentication token and discards the internal password hash. Subsequent calls will raise `PinergyAuthError` immediately.

```python
client.logout()
# client.get_balance()  # This would now raise PinergyAuthError
```

---

## Retrieving Data

### Balance and Meter Status

The `get_balance()` method returns real-time info about your credit and meter.

```python
bal = client.get_balance()

print(f"Current balance: €{bal.credit_balance:.2f}")
print(f"Days remaining:  {bal.top_up_in_days}")
print(f"Meter Reading:   {bal.last_reading:%Y-%m-%d %H:%M}")

if bal.credit_low:
    print("Warning: Credit is low!")
```

### Usage Statistics (Smart/PAYG)

For standard Smart/PAYG accounts, use `get_usage()`. It returns data aggregated into daily, weekly, and monthly buckets.

```python
usage = client.get_usage()

# Daily data for the last 7 days
for day in usage.day:
    print(f"{day.date:%Y-%m-%d}: {day.kwh:.2f} kWh (€{day.amount:.2f})")
```

### Usage Statistics (Level Pay)

If you are a Level Pay customer, use `get_level_pay_usage()` for half-hourly interval data.

```python
lp_usage = client.get_level_pay_usage()
print("Interval labels:", lp_usage.labels[:5])
```

### Comparisons

Compare your usage against the average for similar homes in your area.

```python
cmp = client.compare_usage()
day = cmp.day
print(f"Your usage: {day.kwh.users_home:.1f} kWh")
print(f"Average:    {day.kwh.average_home:.1f} kWh")
```

---

## Configuration and Metadata

### Top-Up Info

View scheduled top-ups and valid top-up amounts.

```python
topups = client.get_active_topups()
for sched in topups.scheduled:
    print(f"Scheduled: €{sched.top_up_amount} on day {sched.top_up_day}")

config = client.get_config_info()
print("Allowed top-up amounts:", config.top_up_amounts)
```

### Notification Preferences

Check how Pinergy contacts you.

```python
prefs = client.get_notification_preferences()
print(f"SMS enabled: {prefs.sms}")
print(f"Email enabled: {prefs.email}")
```

---

## Error Handling

All library exceptions inherit from `PinergyError`.

| Exception | Description |
|---|---|
| `PinergyAuthError` | Authentication failed or session expired. |
| `PinergyAPIError` | The API returned a logical error (e.g., "invalid request"). |
| `PinergyHTTPError` | A network-level or HTTP error occurred. |
| `PinergyTimeoutError` | The request timed out. |
| `PinergyResponseError` | The API returned malformed or unexpected data. |

Example:

```python
from pypinergy.exceptions import PinergyError, PinergyAuthError

try:
    balance = client.get_balance()
except PinergyAuthError:
    print("Please check your credentials.")
except PinergyError as e:
    print(f"An error occurred: {e}")
```

---

## Advanced Usage

### Custom Timeout

You can specify a timeout (in seconds) for all API calls.

```python
client = PinergyClient("email", "password", timeout=10.0)
```

### Proxying and Testing

If you need to route requests through a proxy or a local mock server, override the `base_url`.

```python
client = PinergyClient("email", "password", base_url="http://localhost:8080")
```
