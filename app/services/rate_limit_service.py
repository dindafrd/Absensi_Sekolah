"""Simple in-memory sliding-window rate limiter."""

from collections import defaultdict, deque
from threading import Lock
import time


class RateLimiter:
    """Thread-safe in-memory rate limiter for single-process deployments."""

    _store = defaultdict(deque)
    _lock = Lock()

    @classmethod
    def check(cls, key, limit, window_seconds):
        """Return (allowed, retry_after_seconds)."""
        now = time.time()
        window_start = now - window_seconds

        with cls._lock:
            bucket = cls._store[key]

            while bucket and bucket[0] <= window_start:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after = int(max(1, window_seconds - (now - bucket[0])))
                return False, retry_after

            bucket.append(now)
            return True, 0


def get_client_ip(request):
    """Resolve client IP with support for reverse proxies."""
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        # Use the first hop as originating client.
        return forwarded_for.split(',')[0].strip()
    return (request.remote_addr or 'unknown').strip()
