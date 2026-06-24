"""Unit tests for client-side rate limiting (#196)."""

import time

from pypinergy.client import _TokenBucket


def test_token_bucket_allows_burst():
    bucket = _TokenBucket(rate=100.0, burst=5)
    start = time.monotonic()
    for _ in range(5):
        bucket.acquire()
    elapsed = time.monotonic() - start
    assert elapsed < 0.1


def test_token_bucket_throttles_after_burst():
    bucket = _TokenBucket(rate=100.0, burst=1)
    bucket.acquire()
    start = time.monotonic()
    bucket.acquire()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.005


def test_token_bucket_refills_over_time():
    bucket = _TokenBucket(rate=1000.0, burst=2)
    bucket.acquire()
    bucket.acquire()
    time.sleep(0.01)
    start = time.monotonic()
    bucket.acquire()
    elapsed = time.monotonic() - start
    assert elapsed < 0.05
