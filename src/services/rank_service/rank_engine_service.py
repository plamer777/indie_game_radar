from datetime import datetime, timedelta
from logging import Logger
from src.config import constants as C
from src.db.repositories import GameRepository, GameSnapshotRepository, GamePublicationRepository, IGDBRepository
from src.db.repositories.repositories import NewsPublicationRepository, DiscountPublicationRepository, \
    RankedGameRepository, RedditPostRepository, RankedRedditPostRepository, RedditPostPublicationRepository
from src.models import RankedGameModel, GameModel
from src.schemas import GamePublicationRecordSchema, NewsPublicationSchema, RankedGameSchema, \
    RedditPostPublicationSchema, DiscountPublicationSchema
from src.schemas.reddit_schemas import RankedRedditPostSchema
from src.services.base_service import BaseService
from src.services.shared_dependencies.calculators import NewsStatCalculator
from src.services.rank_service.filters import GameFilter, NewsFilter, DiscountFilter, RedditPostFilter, \
    RedditDevPostFilter, RedditMemeFilter
from src.services.rank_service.rankers import NewsRanker, RedditPostRanker, RedditDevPostRanker, RedditMemeRanker
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
        discount_filter: DiscountFilter,
        discount_publication_repo: DiscountPublicationRepository,
        ranked_games_repo: RankedGameRepository,
        reddit_post_ranker: RedditPostRanker,
        reddit_dev_post_ranker: RedditDevPostRanker,
        reddit_post_repo: RedditPostRepository,
        ranked_reddit_posts_repo: RankedRedditPostRepository,
        reddit_post_filter: RedditPostFilter,
        reddit_post_publication_repo: RedditPostPublicationRepository,
        reddit_dev_post_filter: RedditDevPostFilter,
        reddit_meme_filter: RedditMemeFilter,
        reddit_meme_ranker: RedditMemeRanker,
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
        self._discount_filter = discount_filter
        self._discount_publication_repo = discount_publication_repo
        self._ranked_games_repo = ranked_games_repo
        self._news_stat_calculator = NewsStatCalculator()
        self._reddit_post_ranker = reddit_post_ranker
        self._reddit_post_repo = reddit_post_repo
        self._ranked_reddit_posts_repo = ranked_reddit_posts_repo
        self._reddit_post_filter = reddit_post_filter
        self._reddit_post_publication_repo = reddit_post_publication_repo
        self._reddit_dev_post_ranker = reddit_dev_post_ranker
        self._reddit_dev_post_filter = reddit_dev_post_filter
        self._reddit_meme_ranker = reddit_meme_ranker
        self._reddit_meme_filter = reddit_meme_filter

    async def rank_all(self):
        cycle_log = self._log.bind(method="rank_all")
        cycle_log.info("ranking games and news")
        await self.rank_games()
        await self.rank_game_dev_story_reddit_posts(cycle_log)
        await self.rank_game_meme_reddit_posts(cycle_log)

    async def rank_games(self) -> None:
        """The main method for ranking games.
        """
        cycle_log = self._log.bind(method="rank_games")
        cycle_log.info("cycle_start")
        last_ranked_at = await self._ranked_games_repo.get_max_value("last_ranked_at")
        last_ranked_at = last_ranked_at.get('max_value') or datetime.min
        # d) Скоринг
        games = await self._games.get_all(
            {'updated_at': {'$gte': last_ranked_at}},
            sort_by={'updated_at': -1}, generator_mode=True, show_deleted=True
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
                game.ext_info.news_stats = self._news_stat_calculator.compute_news_stats(game.last_news)
                score = await self._ranker.evaluate(game, meta, snaps)
                ranked_game = RankedGameSchema(
                    **game.model_dump(exclude={'created_at', 'updated_at'}),
                    last_score=score,
                    last_ranked_at=datetime.now()
                )
                self._rank_game_news(ranked_game, cycle_log)
                await self._rank_reddit_posts(ranked_game, cycle_log)
                await self._ranked_games_repo.add_or_update(ranked_game, search_field="steam_appid")

            except Exception as e:
                cycle_log.error("rank_games", exc_info=True, error=e)

    async def filter_games(self, top_n: int) -> list[GamePublicationRecordSchema]:
        cycle_log = self._log.bind(method="filter_games")
        cycle_log.info("started")
        now = datetime.now()
        scored_games = await self._ranked_games_repo.get_all(
            {
                'last_score': {'$gte': C.GAME_FILTER_RATING_MIN},
                '$or': [
                    {"release_date": {"$gte": now - timedelta(days=C.GAME_FILTER_RELEASE_DATE_DELTA_DAYS)}},
                    {"release_date": None}
                ]
            },
            sort_by={'last_score': -1}, generator_mode=True
        )

        unpublished = []
        async for game in scored_games:
            try:
                meta = await self._igdb.get_one({'steam_appid': game.steam_appid})
                was = await self._publish_repo.was_published(game.steam_appid)
                if not was and self._filter.should_publish(game, meta, game.last_score):
                    rec = GamePublicationRecordSchema(**game.model_dump())
                    unpublished.append(rec)
                    if len(unpublished) >= top_n:
                        break
            except Exception as e:
                cycle_log.error("filter_games", exc_info=True, error=e)

        return unpublished

    def _rank_game_news(self, game: RankedGameModel | RankedGameSchema | GameModel, cycle_log: Logger):
        """The method ranks news for a game.
        :param game: The game to rank news for.
        :param cycle_log: The logger to use.
        """
        try:
            now = datetime.now()
            for news in game.last_news:
                news_score = self._news_ranker.evaluate(game, news)
                news.score = news_score
                news.last_ranked_at = now

        except Exception as e:
            cycle_log.error(f"Error ranking news for game {game.steam_appid}: {e}")

    async def _rank_reddit_posts(self, game: RankedGameModel | RankedGameSchema | GameModel, cycle_log: Logger) -> None:
        try:
            reddit_game_related_posts = await self._reddit_post_repo.get_all(
                {'steam_appid': game.steam_appid}, sort_by={'updated_at': -1}, generator_mode=True
            )
            ranked_posts = []
            async for reddit_post in reddit_game_related_posts:
                try:
                    reddit_post_score = self._reddit_post_ranker.evaluate(game, reddit_post)
                    ranked_post = RankedRedditPostSchema(
                        **reddit_post.model_dump(), last_score=reddit_post_score
                    )
                    ranked_posts.append(ranked_post)

                except Exception as e:
                    cycle_log.error(f"Error ranking reddit post {reddit_post.reddit_id}: {e}")

            await self._ranked_reddit_posts_repo.add_or_update(ranked_posts, search_field="reddit_id")

        except Exception as e:
            cycle_log.error(f"Error ranking reddit posts for game {game.steam_appid}: {e}")

    async def rank_game_dev_story_reddit_posts(self, cycle_log: Logger) -> None:
        try:
            max_ranked_date = await self._ranked_reddit_posts_repo.get_max_value(
                field_name='last_ranked_at', params={'type': 'game_dev_story'}
            )
            since = max_ranked_date.get('max_value') or datetime.min
            game_dev_posts = await self._reddit_post_repo.get_all(
                {'type': 'game_dev_story', 'updated_at': {'$gte': since}}, sort_by={'updated_at': -1},
                generator_mode=True
            )
            ranked_posts = []
            async for reddit_post in game_dev_posts:
                try:
                    reddit_post_score = self._reddit_dev_post_ranker.evaluate(reddit_post)
                    ranked_post = RankedRedditPostSchema(
                        **reddit_post.model_dump(), last_score=reddit_post_score
                    )
                    ranked_posts.append(ranked_post)

                except Exception as e:
                    cycle_log.error(f"Error ranking reddit post {reddit_post.reddit_id}: {e}")

            await self._ranked_reddit_posts_repo.add_or_update(ranked_posts, search_field="reddit_id")

        except Exception as e:
            cycle_log.error(f"Error ranking game dev reddit posts: {e}")

    async def rank_game_meme_reddit_posts(self, cycle_log: Logger) -> None:
        try:
            max_ranked_date = await self._ranked_reddit_posts_repo.get_max_value(
                field_name='last_ranked_at', params={'type': 'meme'}
            )
            since = max_ranked_date.get('max_value') or datetime.min
            game_dev_posts = await self._reddit_post_repo.get_all(
                {'type': 'meme', 'updated_at': {'$gte': since}}, sort_by={'updated_at': -1},
                generator_mode=True
            )
            ranked_posts = []
            async for reddit_post in game_dev_posts:
                try:
                    reddit_post_score = self._reddit_meme_ranker.evaluate(reddit_post)
                    ranked_post = RankedRedditPostSchema(
                        **reddit_post.model_dump(), last_score=reddit_post_score
                    )
                    ranked_posts.append(ranked_post)

                except Exception as e:
                    cycle_log.error(f"Error ranking reddit meme post {reddit_post.reddit_id}: {e}")

            await self._ranked_reddit_posts_repo.add_or_update(ranked_posts, search_field="reddit_id")

        except Exception as e:
            cycle_log.error(f"Error ranking game dev reddit posts: {e}")

    async def filter_news(self, top_n: int) -> list[NewsPublicationSchema]:
        cycle_log = self._log.bind(method="filter_news")
        cycle_log.info("started")
        now = datetime.now()
        scored_games = await self._ranked_games_repo.get_all(
            {
                'last_score': {'$gte': C.NEWS_FILTER_GAME_RATING_MIN},
                '$or': [
                    {"release_date": {"$gte": now - timedelta(days=C.NEWS_FILTER_GAME_RELEASE_DATE_DELTA_DAYS)}},
                    {"release_date": None}
                ]
            },
            sort_by={'last_score': -1}, generator_mode=True
        )
        unpublished = []
        async for game in scored_games:
            filtered = []
            for news in game.last_news[:1]:
                was = await self._news_publication_repo.was_published(news.gid)
                if not was:
                    checked_news = await self._news_filter.filter_news([news], game)
                    filtered.extend(checked_news)

            for news in filtered:
                unpublished.append(NewsPublicationSchema(**news.model_dump(), header_image=game.header_image))

                if len(unpublished) >= top_n:
                    break

        return unpublished

    async def filter_reddit_posts(self, top_n: int) -> list[RedditPostPublicationSchema]:
        cycle_log = self._log.bind(method="filter_reddit_posts")
        cycle_log.info("started")
        now = datetime.now()
        scored_games = await self._ranked_games_repo.get_all(
            {
                'last_score': {'$gte': C.REDDIT_FILTER_GAME_RATING_MIN},
                '$or': [
                    {"release_date": {"$gte": now - timedelta(days=C.REDDIT_FILTER_GAME_RELEASE_DATE_DELTA_DAYS)}},
                    {"release_date": None}
                ]
            },
            sort_by={'last_score': -1}, generator_mode=True
        )
        unpublished = []
        async for game in scored_games:
            reddit_posts = await self._ranked_reddit_posts_repo.get_all(
                {'steam_appid': game.steam_appid}, limit=1, sort_by={'created_utc': -1}
            )
            filtered = []
            for post in reddit_posts:
                was = await self._reddit_post_publication_repo.was_published(post)
                if not was:
                    checked_posts = await self._reddit_post_filter.filter_posts([post], game)
                    filtered.extend(checked_posts)

            for post in filtered:
                unpublished.append(RedditPostPublicationSchema(**post.model_dump()))

            if len(unpublished) >= top_n:
                break

        return unpublished

    async def filter_game_dev_reddit_posts(self, top_n: int) -> list[RedditPostPublicationSchema]:
        cycle_log = self._log.bind(method="filter_reddit_posts")
        cycle_log.info("started")

        unpublished = []
        if top_n <= 0:
            return unpublished

        reddit_posts = await self._ranked_reddit_posts_repo.get_all(
            {'type': 'game_dev_story', 'last_score': {'$gte': C.REDDIT_GAME_DEV_FILTER_RATING_MIN}},
            sort_by={'last_score': -1}, generator_mode=True
        )

        async for post in reddit_posts:
            was = await self._reddit_post_publication_repo.was_published(post)
            if was:
                continue
            filtered = await self._reddit_dev_post_filter.filter_posts([post])

            for checked in filtered:
                unpublished.append(RedditPostPublicationSchema(**checked.model_dump()))

                if len(unpublished) >= top_n:
                    break

        return unpublished

    async def filter_game_meme_reddit_posts(self, top_n: int) -> list[RedditPostPublicationSchema]:
        cycle_log = self._log.bind(method="filter_game_meme_reddit_posts")
        cycle_log.info("started")

        unpublished = []
        if top_n <= 0:
            return unpublished

        reddit_posts = await self._ranked_reddit_posts_repo.get_all(
            {'type': 'meme', 'last_score': {'$gte': C.REDDIT_MEME_FILTER_MIN_SCORE}},
            sort_by={'last_score': -1}, generator_mode=True
        )

        async for post in reddit_posts:
            was = await self._reddit_post_publication_repo.was_published(post)
            if was:
                continue

            filtered = self._reddit_meme_filter.filter_posts([post])
            for checked in filtered:
                unpublished.append(RedditPostPublicationSchema(**checked.model_dump()))

                if len(unpublished) >= top_n:
                    break

        return unpublished

    async def filter_discounts(self, top_n: int) -> list[DiscountPublicationSchema]:
        cycle_log = self._log.bind(method="filter_discounts")
        cycle_log.info("started")
        now = datetime.now()
        scored_games = await self._ranked_games_repo.get_all(
            {
                'last_score': {'$gte': C.DISCOUNT_FILTER_GAME_RATING_MIN},
                '$or': [
                    {"release_date": {"$gte": now - timedelta(days=C.DISCOUNT_FILTER_GAME_RELEASE_DATE_DELTA_DAYS)}},
                    {"release_date": None}
                ]
            },
            sort_by={'last_score': -1}, generator_mode=True
        )
        now = datetime.now()
        unpublished = []
        async for game in scored_games:
            try:
                was = await self._discount_publication_repo.was_published(game.steam_appid)
                if was:
                    continue
                snapshots = await self._game_snapshot_repo.get_all(
                    {
                        "steam_appid": game.steam_appid,
                        "snapshot_time": {"$gte": now - timedelta(days=C.DISCOUNT_FILTER_DAYS_LIMIT)}
                    },
                    sort_by={'snapshot_time': -1}
                )
                discount = self._discount_filter.detect_discount(game, snapshots)
                if discount:
                    unpublished.append(discount)

                if len(unpublished) >= top_n:
                    break

            except Exception as e:
                cycle_log.error("filter_discounts", exc_info=True, error=e)

        return unpublished
