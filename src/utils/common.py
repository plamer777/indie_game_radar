import asyncio
import logging
from functools import wraps
from typing import Callable
from uuid import uuid4
# ---------------------------------------------------------------------------------------------------------------------


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    try:
        return a / b if b else default
    except Exception:
        return default


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def execute_in_thread(coro: Callable) -> Callable:
    """The decorator serves to execute any task in separate thread to avoid blocking main program execution
    :param coro: a callable object returning Coroutine to wrap
    """
    @wraps(coro)
    async def wrapper(*args, **kwargs) -> dict[str, str]:
        """The async func is a wrapper to wrap provided coro and execute it in separate thread
        :params args: a positional arguments
        :param kwargs: a keyword arguments
        """
        task_id = str(uuid4())
        kwargs['task_id'] = task_id
        e = None
        for _ in range(3):
            try:
                loop = asyncio.get_running_loop()
                task = loop.create_task(coro(*args, **kwargs))
                task.add_done_callback(
                    lambda t: logging.error("Task failed", exc_info=t.exception()) if t.exception() else None
                )
                break
            except Exception as e:
                kwargs.pop('task_id')
        else:
            if e:
                raise e
        return {'task_id': task_id}

    return wrapper