from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional
from src.orchestrators.strategies import ContentAllocationStrategy
from src.schemas import AllocatedPostsSchema
from src.services.data_service import APIHarvesterService
from src.services.publisher_service import PublisherService
from src.services.rank_service.rank_engine_service import RankEngineService
from src.utils.common import execute_in_thread
from src.config import constants as C
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class Orchestrator:
    def __init__(
        self,
        api_harvester: APIHarvesterService,
        rank_engine: RankEngineService,
        publisher: PublisherService
    ) -> None:
        self._api_harvester = api_harvester
        self._rank_engine = rank_engine
        self._publisher = publisher
        self._log = get_logger().bind(service="orchestrator")

    async def start(self):
        # await self._start_harvester()
        # await self._start_ranker()
        await self._run_cycle(top_n=C.DEFAULT_DAILY_POSTS)

    @execute_in_thread
    async def _start_harvester(self):
        # a) Получаем список appids (будет очень большим). Ограничим первыми N для демо.
        logging.info('harvester_start')
        cycle_log = self._log.bind(service="save_to_db")
        cycle_log.info("cycle_start")

        while True:
            cycle_start = datetime.now()
            cycle_end = cycle_start.replace(hour=12, minute=0, second=0, microsecond=0)

            # если уже после 12 — перенести конец на завтра
            if cycle_end <= cycle_start:
                cycle_end += timedelta(days=1)

            self._log.info(f"starting_cycle_until={cycle_end.isoformat()}")

            try:
                await self._api_harvester.fetch_cycle(until=cycle_end)
            except Exception as e:
                self._log.error("fetch_cycle_error", exc_info=True, error=e)
                await asyncio.sleep(60)  # не спамить при авариях

            # дожидаемся следующего окна (до следующего 12 UTC)
            now = datetime.now()
            if now < cycle_end:
                sleep_seconds = (cycle_end - now).total_seconds()
                self._log.info(f"sleeping_until_next_cycle ({sleep_seconds / 3600:.1f}h)")
                await asyncio.sleep(sleep_seconds)

    @execute_in_thread
    async def _start_ranker(self):
        cycle_log = self._log.bind(service="ranker")
        cycle_log.info("cycle_start")

        while True:
            try:
                await self._rank_engine.rank_all()
            except Exception as e:
                cycle_log.error("ranker_cycle_error", exc_info=True, error=e)

            await asyncio.sleep(C.ORCH_RANKING_INTERVAL)

    async def _allocate_posts(self, top_n: int) -> list[AllocatedPostsSchema]:
        """The method allocates posts to be published
        :param top_n: Number of posts to allocate
        :return: List of allocated posts
        """
        cycle_log = self._log.bind(top_n=top_n)
        cycle_log.info("cycle_start")
        published_today = await self._publisher.count_published_for_today()
        top_n -= published_today
        allocated = []
        for attempt in range(5):
            filtered_reviews_to_publish = await self._rank_engine.filter_reviews(top_n)
            filtered_games_to_publish = await self._rank_engine.filter_games(top_n)
            filtered_news_to_publish = await self._rank_engine.filter_news(top_n)
            filtered_game_leaderboards_to_publish = await self._rank_engine.filter_game_leaderboards(top_n)
            filtered_discounts = await self._rank_engine.filter_discounts(top_n)
            filtered_reddis_posts = await self._rank_engine.filter_reddit_posts(top_n)
            filtered_game_dev_reddit_posts = await self._rank_engine.filter_game_dev_reddit_posts(
                top_n - len(filtered_reddis_posts)
            )
            filtered_game_meme_reddit_posts = await self._rank_engine.filter_game_meme_reddit_posts(top_n)

            filtered_reddis_posts += filtered_game_dev_reddit_posts

            content_strategy = ContentAllocationStrategy(
                games=filtered_games_to_publish, news=filtered_news_to_publish, discounts=filtered_discounts,
                reddit_posts=filtered_reddis_posts, reddit_memes=filtered_game_meme_reddit_posts,
                reviews=filtered_reviews_to_publish,
                game_leaderboards=filtered_game_leaderboards_to_publish
            )
            allocated = content_strategy.schedule_daily_posts(top_n)
            if len(allocated) == top_n:
                break

            await asyncio.sleep(600)

        else:
            cycle_log.warning(
                "not_enough_content_to_publish", total_content=len(allocated)
            )

        return allocated

    async def _run_cycle(self, top_n: Optional[int] = None) -> None:
        """Runs the full ranking and publishing cycle once per day."""
        top_n = top_n or C.DEFAULT_DAILY_POSTS
        while True:
            now = datetime.now(UTC)
            if C.ALLOCATION_START_HOUR <= now.hour < C.ALLOCATION_END_HOUR:
                # --- 1) Распределение ---
                allocated = await self._allocate_posts(top_n)

                # --- 2) Публикации ---
                await self._publisher.schedule_publications(allocated)

                next_run = (now + timedelta(days=1)).replace(
                    hour=C.ALLOCATION_START_HOUR, minute=0, second=0, microsecond=0
                )
                wait_seconds = (next_run - datetime.now(UTC)).total_seconds()
                self._log.info(f"Cycle completed. Next run scheduled at {next_run.isoformat()}")
                await asyncio.sleep(wait_seconds)

            else:
                next_run = now.replace(
                    hour=C.ALLOCATION_START_HOUR, minute=0, second=0, microsecond=0
                )
                if next_run <= now:
                    next_run += timedelta(days=1)

                wait_seconds = (next_run - now).total_seconds()
                self._log.info(f"Outside posting window. Waiting until {next_run.isoformat()}")
                await asyncio.sleep(wait_seconds)
