import asyncio
from datetime import datetime
from typing import Optional
from src.clients import RedditClient
from src.config import constants as C
from src.clients.igdb_client import AsyncIGDBClient
from src.clients.steam_client import AsyncSteamClient
from src.db.repositories import GameRepository, GameSnapshotRepository, AppRepository, IGDBRepository, \
    RedditPostRepository
from src.models.game import GameModel
from src.schemas import GameSnapshotSchema, GameSchema, RedditPostSchema
from src.schemas.igdb_schemas import IGDBMetaSchema
from src.services.base_service import BaseService
from src.services.data_service.adapters import RedditAdapter
from src.services.shared_dependencies import NewsStatCalculator
from src.utils.logging import get_logger
# --------------------------------------------------------------------------------------------------------------------


class APIHarvesterService(BaseService):
    def __init__(
        self,
        steam_client: AsyncSteamClient,
        igdb_client: AsyncIGDBClient,
        reddit_client: RedditClient,
        game_repo: GameRepository,
        reddit_post_repo: RedditPostRepository,
        game_snapshot_repo: GameSnapshotRepository,
        app_repo: AppRepository,
        igdb_repo: IGDBRepository,
    ):
        self._steam = steam_client
        self._igdb_client = igdb_client
        self._reddit_posts = reddit_post_repo
        self._games = game_repo
        self._game_snapshot_repo = game_snapshot_repo
        self._app_repo = app_repo
        self._igdb = igdb_repo
        self._log = get_logger().bind(service="api_harvester")
        self._news_stat_calculator = NewsStatCalculator()
        self._reddit_adapter = RedditAdapter(reddit_client)

    async def fetch_cycle(self, until: datetime) -> None:
        """
        Выполняет инкрементальную выгрузку, пока не наступит заданное время `until`.
        """
        cycle_log = self._log.bind(method="fetch_cycle")
        cycle_log.info("cycle_start")

        # # a) периодически обновляем список app
        await self.fetch_steam_apps()
        # # b) выгружаем свежие посты по ключевым запросам гейм дева и мемы
        await self.fetch_game_dev_reddit_posts()
        await self.fetch_game_meme_reddit_posts()
        # c) выгружаем игры партиями\
        await self.fetch_steam_games(until)

        cycle_log.info("cycle_complete")

    async def fetch_steam_apps(self):
        last_modified = await self._app_repo.get_max_value("last_modified")
        last_modified = last_modified.get('max_value')
        cycle_log = self._log.bind(method="fetch_steam_apps")
        cycle_log.info("start updating apps")
        app_generator = self._steam.fetch_apps(since=last_modified)
        async for app_batch in app_generator:
            try:
                cycle_log.info("fetch_steam_apps", processed=len(app_batch))
                await self._app_repo.add_or_update(app_batch, search_field="appid")
            except Exception as e:
                cycle_log.error("fetch_steam_apps", exc_info=True, error=e)

    async def fetch_steam_games(self, until: datetime | None = None):
        until = until or datetime.min
        cycle_log = self._log.bind(method="fetch_steam_games")
        cycle_log.info("start updating games")
        apps_cursor = await self._app_repo.get_all(sort_by={'last_modified': -1}, generator_mode=True)
        batch = []
        async for app in apps_cursor:
            try:
                if datetime.now() >= until:
                    cycle_log.info("cycle_end_time_reached", processed=len(batch))
                    break

                game = await self._steam.fetch_full_app_details(app.appid)
                if not game:
                    await self._app_repo.delete(app.id)
                    await self._games.delete(app.appid)
                    continue

                changed = await self._games.add_or_update(game, search_field="steam_appid")
                await self.fetch_reddit_posts_by_game(game)

                if changed:
                    total_achievements = len(game.ext_info.achievements or [])
                    avg_unlock_percent = (
                        sum(a.percent for a in game.ext_info.achievements or []) / total_achievements
                        if total_achievements else None
                    )
                    news_stats = self._news_stat_calculator.compute_news_stats(game.last_news)
                    snapshot = GameSnapshotSchema(
                        steam_appid=game.steam_appid,
                        price=game.price.final if game.price else None,
                        discount_percent=game.price.discount_percent if game.price else None,
                        current_players=game.ext_info.current_players,
                        total_achievements=total_achievements,
                        avg_unlock_percent=avg_unlock_percent,
                        review_ratio=game.ext_info.review_summary.ratio if game.ext_info.review_summary else 0,
                        avg_days_per_news=news_stats.avg_interval_days,
                    )
                    await self._game_snapshot_repo.add_new(snapshot.model_dump())

                batch.append(game)
                if len(batch) >= 50:
                    await self._bounded_gather(
                        self.fetch_meta_by_game, batch, concurrency=C.ORCH_FETCH_META_CONCURRENCY
                    )
                    batch.clear()

            except Exception as e:
                cycle_log.error("fetch_steam_games", exc_info=True, error=e)
                await asyncio.sleep(5)

        # если остались необработанные
        if batch:
            await self._bounded_gather(self.fetch_meta_by_game, batch, concurrency=C.ORCH_FETCH_META_CONCURRENCY)

    async def fetch_meta_by_game(self, game: GameSchema | GameModel) -> Optional[IGDBMetaSchema]:
        try:
            meta = await self._igdb_client.fetch_game_meta(name=game.name, steam_appid=game.steam_appid)
            if meta:
                meta.steam_appid = game.steam_appid
                await self._igdb.add_or_update(meta, search_field="steam_appid")

            return meta
        except Exception as e:
            self._log.error("fetch_meta_by_game", exc_info=True, error=e)
            return None

    async def fetch_reddit_posts_by_game(self, game: GameSchema | GameModel) -> list[RedditPostSchema]:
        try:
            reddit_posts = await self._reddit_adapter.search_posts_for_game(
                steam_appid=game.steam_appid
            )
            [setattr(post, 'game_name', game.name) for post in reddit_posts]
            await self._reddit_posts.add_or_update(reddit_posts, search_field="reddit_id")

            return reddit_posts
        except Exception as e:
            self._log.error("fetch_reddit_posts_by_game", exc_info=True, error=e)
            return []

    async def fetch_game_dev_reddit_posts(self) -> list[RedditPostSchema]:
        cycle_log = self._log.bind(method="fetch_reddit_posts")
        cycle_log.info("start updating game dev reddit posts")
        try:
            reddit_posts = await self._reddit_adapter.fetch_meta_indie_posts()
            await self._reddit_posts.add_or_update(reddit_posts, search_field="reddit_id")
            cycle_log.info("fetched game dev reddit posts", processed=len(reddit_posts))
            return reddit_posts
        except Exception as e:
            cycle_log.error("fetch_game_dev_reddit_posts", exc_info=True, error=e)
            return []

    async def fetch_game_meme_reddit_posts(self) -> list[RedditPostSchema]:
        cycle_log = self._log.bind(method="fetch_reddit_posts")
        cycle_log.info("start updating game_meme_reddit_posts")
        try:
            reddit_posts = await self._reddit_adapter.fetch_gaming_memes()
            await self._reddit_posts.add_or_update(reddit_posts, search_field="reddit_id")
            cycle_log.info("fetched game meme reddit posts", processed=len(reddit_posts))
            return reddit_posts
        except Exception as e:
            cycle_log.error("fetch_game_dev_reddit_posts", exc_info=True, error=e)
            return []
