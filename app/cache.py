"""In-memory TTL cache for slow upstream data."""
import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Keeps the last successful value for `ttl` seconds.

    Concurrent misses share one load, so an expired entry costs a single upstream
    call instead of one per waiting request.
    """

    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self.value: T | None = None
        self._stamp = 0.0
        self._lock = asyncio.Lock()

    def _fresh(self) -> bool:
        return self.value is not None and time.monotonic() - self._stamp < self.ttl

    async def get(self, load: Callable[[], Awaitable[T | None]]) -> T | None:
        """The fresh value, else the result of `load()`.

        A `None` result or an exception from `load()` leaves the previous value in
        `self.value`, so callers can still serve it as stale data.
        """
        if self._fresh():
            return self.value
        async with self._lock:
            if self._fresh():
                return self.value
            value = await load()
            if value is not None:
                self.value, self._stamp = value, time.monotonic()
            return value
