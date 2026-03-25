"""monitor_balance.py — Poll the balance and print an alert when credit is low.

Useful as a cron job or background script.

Usage:
    python examples/monitor_balance.py

Environment variables:
    PINERGY_EMAIL     — required
    PINERGY_PASSWORD  — required
    PINERGY_THRESHOLD — alert when balance drops below this (default: 10.0)
"""

import os
import sys
from pypinergy import PinergyClient
from pypinergy.exceptions import PinergyError

EMAIL = os.environ.get("PINERGY_EMAIL")
PASSWORD = os.environ.get("PINERGY_PASSWORD")
THRESHOLD = float(os.environ.get("PINERGY_THRESHOLD", "10.0"))


def main():
    if not EMAIL or not PASSWORD:
        print("Set PINERGY_EMAIL and PINERGY_PASSWORD environment variables.")
        sys.exit(1)

    client = PinergyClient(EMAIL, PASSWORD)

    try:
        bal = client.get_balance()
    except PinergyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    print(f"Balance: €{bal.balance:.2f} | Days remaining: {bal.top_up_in_days}")

    alerts = []
    if bal.power_off:
        alerts.append("POWER IS OFF — supply disconnected!")
    if bal.emergency_credit:
        alerts.append("On emergency credit!")
    if bal.credit_low:
        alerts.append("Credit is below configured threshold.")
    if bal.balance < THRESHOLD:
        alerts.append(
            f"Balance €{bal.balance:.2f} is below your alert threshold of €{THRESHOLD:.2f}."
        )

    if alerts:
        print()
        for alert in alerts:
            print(f"  ALERT: {alert}")
        sys.exit(1)  # non-zero exit so cron / monitoring picks it up

    print("All clear.")


if __name__ == "__main__":
    main()
