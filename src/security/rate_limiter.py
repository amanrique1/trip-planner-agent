from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from config import get_settings

settings = get_settings()


class SlidingWindowRateLimiter:
    """
    Thread-safe in-memory sliding-window rate limiter.

    For production, replace the in-memory store with Redis
    (e.g. using `redis-py` with a Lua script for atomicity).
    """

    def __init__(
        self,
        max_requests: int = settings.rate_limit_requests,
        window_seconds: int = settings.rate_limit_window_seconds,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(self, identifier: str) -> tuple[bool, int]:
        """
        Check whether *identifier* (username or IP) may make another request.

        Returns:
            (allowed, retry_after_seconds)
        """
        now = time.monotonic()
        cutoff = now - self._window_seconds

        with self._lock:
            bucket = self._buckets[identifier]

            # Evict timestamps outside the window
            while bucket and bucket[0] < cutoff:
                bucket.popleft()

            if len(bucket) >= self._max_requests:
                oldest = bucket[0]
                retry_after = int(self._window_seconds - (now - oldest)) + 1
                return False, retry_after

            bucket.append(now)
            return True, 0

    def reset(self, identifier: str) -> None:
        with self._lock:
            self._buckets.pop(identifier, None)


# Singleton — shared across the whole process
rate_limiter = SlidingWindowRateLimiter()