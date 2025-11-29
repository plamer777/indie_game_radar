import asyncio
from datetime import datetime
from typing import Optional
from src.clients import RedditClient, SpeedrunClient
from src.config import constants as C
from src.clients.igdb_client import AsyncIGDBClient
from src.clients.steam_client import AsyncSteamClient
from src.db.repositories import GameRepository, GameSnapshotRepository, AppRepository, IGDBRepository, \
    RedditPostRepository, LeaderboardRepository, RankedGameRepository
from src.models.game import GameModel
from src.schemas import GameSnapshotSchema, GameSchema, RedditPostSchema, GameLeaderboardSchema
from src.schemas.igdb_schemas import IGDBMetaSchema
from src.services.base_service import BaseService
from src.services.data_service.adapters import RedditAdapter, SpeedrunAdapter
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
        speedrun_client: SpeedrunClient,
        leaderboard_repo: LeaderboardRepository,
        ranked_games_repo: RankedGameRepository,
    ) -> None:
        """The constructor method for APIHarvesterService class.
        :param steam_client: an instance of AsyncSteamClient class
        :param igdb_client: an instance of AsyncIGDBClient class
        :param reddit_client: an instance of RedditClient class
        :param game_repo: an instance of GameRepository class
        :param reddit_post_repo: an instance of RedditPostRepository class
        :param game_snapshot_repo: an instance of GameSnapshotRepository class
        :param app_repo: an instance of AppRepository class
        :param igdb_repo: an instance of IGDBRepository class
        :param speedrun_client: an instance of SpeedrunClient class
        :param leaderboard_repo: an instance of LeaderboardRepository class
        :param ranked_games_repo: an instance of RankedGameRepository class
        """
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
        self._speedrun_adapter = SpeedrunAdapter(speedrun_client)
        self._leaderboard_repo = leaderboard_repo
        self._ranked_games_repo = ranked_games_repo

    async def fetch_cycle(self, until: datetime) -> None:
        """
        Выполняет инкрементальную выгрузку, пока не наступит заданное время `until`.
        """
        cycle_log = self._log.bind(method="fetch_cycle")
        cycle_log.info("cycle_start")

        # a) периодически обновляем список app
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
                    await self._games.delete({"steam_appid": app.appid})
                    continue

                changed = await self._games.add_or_update(game, search_field="steam_appid")
                await asyncio.gather(*[self.fetch_game_leaderboard(game), self.fetch_reddit_posts_by_game(game)])

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
        """The method serves to fetch meta for a game
        :param game: an instance of GameSchema or GameModel class
        :return: an instance of IGDBMetaSchema class or None if game was not found
        """
        try:
            meta = await self._igdb_client.fetch_game_meta(name=game.name, steam_appid=game.steam_appid)
            if meta:
                meta.steam_appid = game.steam_appid
                await self._igdb.add_or_update(meta, search_field="steam_appid")

            return meta
        except Exception as e:
            self._log.error("fetch_meta_by_game", exc_info=True, error=e)
            return None

    async def fetch_game_leaderboard(self, game: GameSchema | GameModel) -> Optional[GameLeaderboardSchema]:
        """The method serves to fetch leaderboard for a game
        :param game: an instance of GameSchema or GameModel class
        :return: an instance of GameLeaderboardSchema class or None if game was not found
        """
        try:
            leaderboard = await self._speedrun_adapter.fetch_leaderboard(game_name=game.name)
            if leaderboard and game.release_date:
                if abs((leaderboard.release_date - game.release_date).days) > C.SPEEDRUN_GAME_RELEASE_MAX_DELTA_DAYS:
                    return None
                leaderboard.steam_appid = game.steam_appid
                await self._leaderboard_repo.add_or_update(leaderboard, search_field="steam_appid")

            return leaderboard
        except Exception as e:
            self._log.error("fetch_game_leaderboard", exc_info=True, error=e)
            return None

    async def fetch_reddit_arts_by_game(self, game: GameSchema | GameModel) -> list[RedditPostSchema]:
        try:
            # TODO method don't works for now, not any art found for games
            reddit_posts = await self._reddit_adapter.fetch_game_pixel_art(
                game_names=[game.name]
            )
            [setattr(post, 'game_name', game.name) for post in reddit_posts]
            await self._reddit_posts.add_or_update(reddit_posts, search_field="reddit_id")

            return reddit_posts
        except Exception as e:
            self._log.error("fetch_reddit_posts_by_game", exc_info=True, error=e)
            return []

    async def fetch_reddit_posts_by_game(self, game: GameSchema | GameModel) -> list[RedditPostSchema]:
        """The method serves to fetch and save reddit posts related to provided game object
        :param game: an instance of GameSchema or GameModel class
        :return: a list of RedditPostSchema objects or empty list if no posts were found
        """
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
        """The method serves to fetch and save reddit posts related to game dev theme
        :return: a list of RedditPostSchema objects or empty list if no posts were found
        """
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
        """The method serves to fetch and save reddit posts related to game meme theme
        :return: a list of RedditPostSchema objects or empty list if no posts were found
        """
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

    async def delete_stage_data(
        self, until: datetime | None = None, game_snapshot_score_lt: int | None = C.HARVESTER_SNAPSHOT_MIN_GAME_SCORE,
        min_ranked_games_count: int = C.HARVESTER_MIN_RANKED_GAMES_COUNT_TO_DELETE_SNAPSHOTS
    ) -> None:
        """The method serves to delete stage data such as games, reddit posts and game snapshots depending on provided
        params
        :param until: datetime to delete data until
        :param game_snapshot_score_lt: minimum score to delete game snapshots
        :param min_ranked_games_count: minimum number of ranked games to delete snapshots
        """
        cycle_log = self._log.bind(method="delete_stage_data")
        cycle_log.info("start deleting stage data")
        until = until or datetime.now()
        try:
            await self._games.delete({'updated_at': {'$lt': until}}, many=True, delete_permanently=True)
            await self._reddit_posts.delete({'updated_at': {'$lt': until}}, many=True, delete_permanently=True)
            ranked_games = await self._ranked_games_repo.get_all({'last_score': {'$gte': game_snapshot_score_lt}})
            if len(ranked_games) >= min_ranked_games_count:
                game_ids = [game.steam_appid for game in ranked_games]
                await self._game_snapshot_repo.delete(
                    {'steam_appid': {'$nin': game_ids}}, many=True, delete_permanently=True
                )

            cycle_log.info("Stage data deleted successfully")

        except Exception as e:
            cycle_log.error("delete_stage_data", exc_info=True, error=e)

