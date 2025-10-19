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

    def repeat_execution_async(
        self,
        attempts: int = 3, ignore_errors: bool = True,
        log_results: bool = True, delay: int = 0,
        attempt_if_not_result: bool = False
    ) -> any:
        """This decorator is used try to use a few attempts to execute a wrapped
        function
        :param ignore_errors: a boolean representing whether to return the result as None if any error occurs during
        making request or raise an exception then all attempts are over if ignore_errors is False
        :param attempts: an integer representing the number of attempts to execute
        the wrapped function
        :param delay: an integer representing the delay in seconds between attempts
        to execute the wrapped function
        :param attempt_if_not_result: a boolean representing whether to execute
        the wrapped function one more time if the result is equal to bool(False)
        :param log_results: a boolean representing whether to log the results
        """

        def decorator(func):
            async def wrapper(*args, **kwargs):
                result = None
                e = None
                for _ in range(abs(attempts) or 1):
                    try:
                        result = await func(*args, **kwargs)
                        if attempt_if_not_result and not result:
                            raise ValueError(
                                f'The function {func.__name__} returned no result')
                        if log_results:
                            logging.info(
                                f'Async function completed successfully:'
                                f' {func.__name__}')
                        return result

                    except Exception as error:
                        e = error
                        await asyncio.sleep(abs(delay))
                        if log_results:
                            logging.error(
                                f'Async function: {func.__name__}, kwargs:'
                                f' {kwargs}, interrupted with error: {e}')

                if not ignore_errors and e:
                    raise e

                return result

            return wrapper

        return decorator

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
