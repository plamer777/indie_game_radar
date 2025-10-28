from __future__ import annotations
import asyncio
import logging
import random
from typing import Type, Iterable, Any, Awaitable, Callable
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class RetryPolicy:
    def __init__(
        self,
        retries: int = C.DEFAULT_RETRY_ATTEMPTS,
        base_delay: float = C.DEFAULT_RETRY_BASE_DELAY,
        max_delay: float = C.DEFAULT_RETRY_MAX_DELAY,
        retry_exceptions: Iterable[Type[BaseException]] = (Exception,),
        jitter: float = C.DEFAULT_RETRY_JITTER,
    ) -> None:
        self.retries = retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_exceptions = tuple(retry_exceptions)
        self.jitter = jitter

    async def run(self, coro: Callable[[], Awaitable[Any]]) -> Any:
        last_exc = None
        for attempt in range(self.retries + 1):
            try:
                return await coro()
            except self.retry_exceptions as exc:  # type: ignore[misc]
                last_exc = exc
                if attempt >= self.retries:
                    break
                delay = min(self.max_delay, self.base_delay * (2 ** attempt))
                # apply jitter factor
                delay *= 1.0 + random.uniform(-self.jitter, self.jitter)
                await asyncio.sleep(delay)
        return None
