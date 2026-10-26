from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar


Result = TypeVar("Result")


def retry_transient(
    operation: Callable[[], Result],
    max_attempts: int = 3,
    delay_seconds: float = 0.5,
    sleeper: Callable[[float], None] = time.sleep,
) -> Result:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if delay_seconds < 0:
        raise ValueError("delay_seconds cannot be negative")

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except OSError:
            if attempt == max_attempts:
                raise
            sleeper(delay_seconds)

    raise RuntimeError("Retry loop exited without a result")
