import asyncio
from typing import Sequence
# ---------------------------------------------------------------------------------------------------------------------


class BaseService:
    async def _bounded_gather(self,func, iterable: Sequence, concurrency: int = 10):
        sem = asyncio.Semaphore(concurrency)

        async def worker(item):
            async with sem:
                return await func(item)

        await asyncio.gather(*(worker(i) for i in iterable))