from __future__ import annotations
import asyncio
from src.config.constants import SCHED_FIXED_HOURS_DEFAULT
from src.config import settings
from src.db.repositories import AppRepository, GameSnapshotRepository
from src.utils.logging import configure_logging, get_logger
from src.managers.cache import RedisCache
from src.db.mongo import ensure_indexes
from src.db.repositories import GameRepository, IGDBRepository, PublicationRepository
from src.clients.steam_client import AsyncSteamClient
from src.clients.igdb_client import AsyncIGDBClient
from src.clients.telegram_client import TelegramPublisher
from src.services.rank_service.rankers.ranker import GameRanker
from src.services.rank_service.filters.filter import GameFilter
from src.services.orchestrator import Orchestrator
from src.scheduler.scheduler import AsyncScheduler
# ---------------------------------------------------------------------------------------------------------------------


async def app_main() -> None:
    configure_logging()
    log = get_logger().bind(app="igr")
    log.info("app_start")

    # Redis
    cache = RedisCache()

    # Mongo
    await ensure_indexes()

    # Clients/services
    steam = AsyncSteamClient(cache)
    igdb = AsyncIGDBClient(cache)
    tg = TelegramPublisher()
    ranker = GameRanker()
    gfilter = GameFilter()

    games_repo = GameRepository()
    igdb_repo = IGDBRepository()
    pub_repo = PublicationRepository()
    app_repo = AppRepository()
    game_snapshot_repo = GameSnapshotRepository()

    orchestrator = Orchestrator(
        games_repo=games_repo,
        igdb_repo=igdb_repo,
        pub_repo=pub_repo,
        steam=steam,
        igdb=igdb,
        publisher=tg,
        ranker=ranker,
        game_filter=gfilter,
        app_repo=app_repo,
        game_snapshot_repo=game_snapshot_repo,
    )

    await orchestrator.save_to_db()

    async def run_once():
        try:
            await orchestrator.run_cycle(top_n=settings.TOP_N_TO_PUBLISH)
        except Exception as e:
            log.error("cycle_error", error=str(e))

    if settings.ONE_SHOT or settings.RUN_INTERVAL_SECONDS <= 0:
        await run_once()
    else:
        scheduler = AsyncScheduler()
        try:
            await scheduler.run_fixed_hours(run_once, SCHED_FIXED_HOURS_DEFAULT)
        except asyncio.CancelledError:
            pass

    # graceful close
    await steam.close()
    await igdb.close()
    await tg.close()
    log.info("app_stop")


if __name__ == "__main__":
    asyncio.run(app_main())
