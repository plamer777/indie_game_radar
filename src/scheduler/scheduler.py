from __future__ import annotations
import asyncio
from typing import Awaitable, Callable
from src.config.constants import SCHED_FIXED_HOURS_DEFAULT
from src.utils.common import execute_in_thread
from src.utils.logging import get_logger
from src.config import constants as C
from datetime import datetime, timedelta
# ---------------------------------------------------------------------------------------------------------------------


class AsyncScheduler:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._running = False
        self._log = get_logger().bind(service="scheduler")

    def stop(self) -> None:
        self._running = False

    @execute_in_thread
    async def run_fixed_hours(
        self, task: Callable[[], Awaitable[None]], hours: list[int] = SCHED_FIXED_HOURS_DEFAULT
    ) -> None:
        """Run task at specific local hours every day (minute=0, second=0).

        Args:
            hours: list of hours [0..23]; if None uses C.SCHED_FIXED_HOURS_DEFAULT.
            task: async callable to run.
        """
        schedule_hours = sorted(set(hours))
        # validate
        schedule_hours = [h for h in schedule_hours if 0 <= h <= 23]
        if not schedule_hours:
            raise ValueError("No valid hours provided for scheduler")

        self._running = True
        self._log.info("scheduler_start_fixed", hours=schedule_hours)
        try:
            while self._running:
                now = datetime.now()
                # compute next run time today or tomorrow at hh:00:00
                next_run = None
                for h in schedule_hours:
                    candidate = now.replace(hour=h, minute=0, second=0, microsecond=0)
                    if candidate > now:
                        next_run = candidate
                        break
                if next_run is None:
                    # earliest hour tomorrow
                    next_run = (now + timedelta(days=1)).replace(
                        hour=schedule_hours[0], minute=0, second=0, microsecond=0
                    )

                sleep_seconds = max(C.SCHED_MIN_SLEEP_SECONDS, (next_run - now).total_seconds())
                await asyncio.sleep(sleep_seconds)

                if not self._running:
                    break

                if self._lock.locked():
                    self._log.warning("skip_overlap")
                    continue
                async with self._lock:
                    await task()
        finally:
            self._log.info("scheduler_stop_fixed")
