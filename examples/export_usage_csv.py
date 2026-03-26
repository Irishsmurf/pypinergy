"""export_usage_csv.py — Export daily usage history to a CSV file.

Usage:
    python examples/export_usage_csv.py > usage.csv
    python examples/export_usage_csv.py --period week > weekly.csv

Periods: day (default), week, month
"""

import argparse
import csv
import os
import sys
from pypinergy import PinergyClient
from pypinergy.exceptions import PinergyError

EMAIL = os.environ.get("PINERGY_EMAIL")
PASSWORD = os.environ.get("PINERGY_PASSWORD")


def main():
    parser = argparse.ArgumentParser(description="Export Pinergy usage to CSV")
    parser.add_argument(
        "--period",
        choices=["day", "week", "month"],
        default="day",
        help="Granularity of the export (default: day)",
    )
    args = parser.parse_args()

    if not EMAIL or not PASSWORD:
        print(
            "Set PINERGY_EMAIL and PINERGY_PASSWORD environment variables.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = PinergyClient(EMAIL, PASSWORD)

    try:
        usage = client.get_usage()
    except PinergyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    entries = getattr(usage, args.period)

    writer = csv.writer(sys.stdout)
    writer.writerow(["date", "kwh", "amount_eur", "co2_kg", "available"])
    for entry in entries:
        writer.writerow(
            [
                entry.date.strftime("%Y-%m-%d"),
                f"{entry.kwh:.4f}",
                f"{entry.amount:.4f}",
                f"{entry.co2:.4f}",
                entry.available,
            ]
        )


if __name__ == "__main__":
    main()
