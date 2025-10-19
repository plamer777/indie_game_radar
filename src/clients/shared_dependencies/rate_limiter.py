from __future__ import annotations
import asyncio
import time
# ---------------------------------------------------------------------------------------------------------------------


class SemaphoreLimiter:
    def __init__(self, max_concurrency: int) -> None:
        self._sem = asyncio.Semaphore(max_concurrency)

    async def __aenter__(self):
        await self._sem.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._sem.release()


class TokenBucket:
    def __init__(self, rate_per_sec: float, capacity: int) -> None:
        self.rate = rate_per_sec
        self.capacity = capacity
        self.tokens = capacity
        self.timestamp = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.timestamp
                self.timestamp = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
                # need to wait for more tokens
                needed = tokens - self.tokens
                wait_time = needed / self.rate if self.rate > 0 else 0.1
                await asyncio.sleep(wait_time)
