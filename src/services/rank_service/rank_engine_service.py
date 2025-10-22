from datetime import datetime, timedelta
from src.config import constants as C
from src.db.repositories import GameRepository, GameSnapshotRepository, GamePublicationRepository, IGDBRepository
from src.db.repositories.repositories import NewsPublicationRepository
from src.schemas import GameGamePublicationRecordSchema, NewsPublicationSchema
from src.services.base_service import BaseService
from src.services.rank_service.filters.filter import GameFilter
from src.services.rank_service.filters.news_filter import NewsFilter
from src.services.rank_service.rankers import NewsRanker
from src.services.rank_service.rankers.ranker import GameRanker
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class RankEngineService(BaseService):

    def __init__(
        self, games_repo: GameRepository, game_snapshot_repo: GameSnapshotRepository,
        publish_repo: GamePublicationRepository,
        igdb_repo: IGDBRepository,
        game_ranker: GameRanker,
        game_filter: GameFilter,
        news_ranker: NewsRanker,
        news_filter: NewsFilter,
        news_publication_repo: NewsPublicationRepository,
    ):
        super().__init__()
        self._log = get_logger().bind(service="rank_engine")
        self._games = games_repo
        self._game_snapshot_repo = game_snapshot_repo
        self._publish_repo = publish_repo
        self._igdb = igdb_repo
        self._ranker = game_ranker
        self._filter = game_filter
        self._news_ranker = news_ranker
        self._news_filter = news_filter
        self._news_publication_repo = news_publication_repo

    async def rank_all(self):
        cycle_log = self._log.bind(method="rank_all")
        cycle_log.info("ranking games and news")
        await self.rank_games()
        await self.rank_news()

    async def rank_games(self) -> None:
        """The main method for ranking games.
        """
        cycle_log = self._log.bind(method="rank_games")
        cycle_log.info("cycle_start")
        last_ranked_at = await self._games.get_max_value("last_ranked_at")
        last_ranked_at = last_ranked_at.get('max_value') or datetime.min
        # d) Скоринг
        games = await self._games.get_all(
            {'$or': [{'updated_at': {'$gte': last_ranked_at}}, {'last_score': None}]},
            sort_by={'updated_at': -1}, generator_mode=True
        )
        now = datetime.now()
        period_days = 45  # параметр можно вынести в настройки
        start_date = now - timedelta(days=period_days)

        async for game in games:
            try:
                meta = await self._igdb.get_one({'steam_appid': game.steam_appid})
                snaps = await self._game_snapshot_repo.get_all(
                    {
                        "steam_appid": game.steam_appid,
                        "snapshot_time": {"$gte": start_date}
                    },
                    sort_by={'snapshot_time': -1}
                )
                score = await self._ranker.evaluate(game, meta, snaps)
                await self._games.update_score(game.steam_appid, score)

            except Exception as e:
                cycle_log.error("rank_games", exc_info=True, error=e)

    async def filter_games(self, top_n: int) -> int:
        cycle_log = self._log.bind(method="filter_games")
        cycle_log.info("started")
        scored_games = await self._games.get_all(
            {'last_score': {'$ne': None}}, sort_by={'last_score': -1}, generator_mode=True
        )
        unpublished = []
        async for game in scored_games:
            try:
                meta = await self._igdb.get_one({'steam_appid': game.steam_appid})
                if self._filter.should_publish(game, meta, game.last_score):
                    was = await self._publish_repo.was_published(game.steam_appid)
                    if not was:
                        rec = GameGamePublicationRecordSchema(
                            steam_appid=game.steam_appid, score_at_publish=game.last_score
                        )
                        unpublished.append(rec)
                    if len(unpublished) >= top_n:
                        await self._publish_repo.add_or_update(unpublished, search_field="steam_appid")
                        break
            except Exception as e:
                cycle_log.error("filter_games", exc_info=True, error=e)

        else:
            await self._publish_repo.add_or_update(unpublished, search_field="steam_appid")

        return len(unpublished)

    async def rank_news(self) -> None:
        cycle_log = self._log.bind(method="rank_news")
        cycle_log.info("cycle_start")
        last_ranked_at = await self._games.get_max_value("last_news.last_ranked_at")
        last_ranked_at = last_ranked_at.get('max_value') or datetime.min
        games = await self._games.get_all(
            {'$or': [{'updated_at': {'$gte': last_ranked_at}}, {'last_news.last_ranked_at': None}]},
            sort_by={'last_score': -1}, generator_mode=True
        )
        updated = []
        async for game in games:
            try:
                now = datetime.now()
                for news in game.last_news:
                    news_score = self._news_ranker.evaluate(game, news)
                    news.score = news_score
                    news.last_ranked_at = now
                game.updated_at = now
                updated.append(game)
                if len(updated) >= C.ORCH_NEWS_RANKING_BATCH_SIZE:
                    await self._games.add_or_update(updated, search_field="steam_appid")
                    updated.clear()
            except Exception as e:
                cycle_log.error(f"Error ranking news for game {game.steam_appid}: {e}")

        await self._games.add_or_update(updated, search_field="steam_appid")

    async def filter_news(self, top_n: int) -> int:
        cycle_log = self._log.bind(method="filter_news")
        cycle_log.info("started")
        scored_games = await self._games.get_all(
            {'last_score': {'$ne': None}}, sort_by={'last_score': -1}, generator_mode=True
        )
        unpublished = []
        async for game in scored_games:
            filtered = await self._news_filter.filter_news(game.last_news)
            unpublished.extend(filtered)
            if len(unpublished) >= top_n:
                break

        for news in unpublished:
            new_publication = NewsPublicationSchema(**news.model_dump())
            await self._news_publication_repo.add_or_update(new_publication, search_field="gid")

        return len(unpublished)
