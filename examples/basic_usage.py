"""basic_usage.py — Get started with pypinergy in under 30 lines.

Usage:
    python examples/basic_usage.py
"""

import os
from pypinergy import PinergyClient

EMAIL = os.environ.get("PINERGY_EMAIL", "you@example.com")
PASSWORD = os.environ.get("PINERGY_PASSWORD", "your-password")


def main():
    client = PinergyClient(EMAIL, PASSWORD)

    # --- Account info -------------------------------------------------------
    login = client.login()
    print(f"Hello, {login.user.first_name} {login.user.last_name}!")
    print(f"Account type : {login.account_type}")
    print(f"Premises     : {login.premises_number}")
    print(f"Level pay    : {login.is_level_pay}")
    print()

    # --- Balance ------------------------------------------------------------
    bal = client.get_balance()
    print(f"Balance      : €{bal.balance:.2f}")
    print(f"Days left    : {bal.top_up_in_days}")
    if bal.credit_low:
        print("  ⚠  Credit is low!")
    if bal.emergency_credit:
        print("  ⚠  On emergency credit!")
    print()

    # --- Today's usage ------------------------------------------------------
    usage = client.get_usage()
    print("Last 7 days:")
    for entry in usage.day:
        marker = "<--" if entry == usage.day[0] else ""
        print(f"  {entry.date:%Y-%m-%d}  {entry.kwh:5.2f} kWh  €{entry.amount:.2f}  {marker}")
    print()

    # --- Compare ------------------------------------------------------------
    cmp = client.compare_usage()
    d = cmp.day
    if d.available:
        diff = d.kwh.users_home - d.kwh.average_home
        direction = "more" if diff > 0 else "less"
        print(
            f"Today vs similar homes: "
            f"{d.kwh.users_home:.2f} kWh vs avg {d.kwh.average_home:.2f} kWh "
            f"({abs(diff):.2f} kWh {direction})"
        )


if __name__ == "__main__":
    main()
