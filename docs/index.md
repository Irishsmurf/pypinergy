# PyPinergy Documentation

Welcome to the documentation for **PyPinergy**, an unofficial Python client library for the Pinergy smart-meter API.

## Key Features

- **Lazy Authentication:** Client logs in automatically when needed.
- **Smart/PAYG Support:** Detailed usage data (daily, weekly, monthly).
- **Balance Tracking:** Credit balance, estimated days remaining, and meter readings.
- **Top-Ups:** View scheduled and auto top-ups.
- **Usage Comparison:** Compare your usage against similar homes.

## Installation

```bash
pip install pypinergy
```

## Quick Start

```python
from pypinergy import PinergyClient

with PinergyClient("email", "password") as client:
    print(client.get_balance())
```
