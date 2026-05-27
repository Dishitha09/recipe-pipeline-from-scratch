from __future__ import annotations

import time
from typing import Callable, TypeVar


T = TypeVar("T")


def retry(
    func: Callable[[], T],
    retries: int = 3,
    delay: float = 2.0,
) -> T:
    last_exception = None

    for attempt in range(1, retries + 1):
        try:
            return func()

        except Exception as exc:
            last_exception = exc

            print(
                f"[RETRY] attempt={attempt}/{retries} failed :: {exc}"
            )

            if attempt < retries:
                time.sleep(delay)

    raise last_exception