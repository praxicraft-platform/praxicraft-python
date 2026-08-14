"""Retry helpers for transient Public API failures."""

from __future__ import annotations

import email.utils
import random
import time
from datetime import datetime, timezone
from typing import Callable

DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_BASE_SECONDS = 0.5
DEFAULT_RETRY_CAP_SECONDS = 8.0

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def should_retry_status(status_code: int) -> bool:
    return status_code in RETRYABLE_STATUS_CODES


def parse_retry_after_seconds(value: str | None) -> float | None:
    """Parse ``Retry-After`` as delay-seconds or HTTP-date → seconds from now."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        seconds = float(text)
        return max(0.0, seconds)
    except (TypeError, ValueError):
        pass
    try:
        # email.utils.parsedate_to_datetime handles RFC 1123 / 850 / asctime
        when = email.utils.parsedate_to_datetime(text)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        delta = (when - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, delta)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def retry_delay_seconds(attempt: int, retry_after_header: str | None) -> float:
    parsed = parse_retry_after_seconds(retry_after_header)
    if parsed is not None:
        return min(parsed, DEFAULT_RETRY_CAP_SECONDS)
    ceiling = min(
        DEFAULT_RETRY_CAP_SECONDS,
        DEFAULT_RETRY_BASE_SECONDS * (2**attempt),
    )
    return random.uniform(0.0, ceiling)


# Overridable in tests.
sleep_fn: Callable[[float], None] = time.sleep
