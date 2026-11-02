from __future__ import annotations
import asyncio
# ---------------------------------------------------------------------------------------------------------------------


class SemaphoreLimiter:
    def __init__(self, max_concurrency: int) -> None:
        self._sem = asyncio.Semaphore(max_concurrency)

    async def __aenter__(self):
        await self._sem.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._sem.release()
