# PyPinergy

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/dark_logo.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/brand/logo.svg">
    <img alt="PyPinergy Logo" src="assets/brand/logo.svg" width="550">
  </picture>
</p>

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
