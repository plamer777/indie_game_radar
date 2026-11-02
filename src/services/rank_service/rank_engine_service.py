from datetime import datetime, timedelta
from logging import Logger
from openai import AsyncOpenAI
from src.config import constants as C
from src.db.repositories import GameRepository, GameSnapshotRepository, GamePublicationRepository, IGDBRepository, \
    CheckedEntityRepository
from src.db.repositories.repositories import NewsPublicationRepository, DiscountPublicationRepository, \
    RankedGameRepository, RedditPostRepository, RankedRedditPostRepository, RedditPostPublicationRepository, \
    ReviewPublicationRepository, GameLeaderboardPublicationRepository, LeaderboardRepository
from src.models import RankedGameModel, GameModel
from src.schemas import GamePublicationRecordSchema, NewsPublicationSchema, RankedGameSchema, \
    RedditPostPublicationSchema, DiscountPublicationSchema, ReviewPublicationSchema, GameLeaderboardPublicationSchema
from src.schemas.reddit_schemas import RankedRedditPostSchema
from src.services.base_service import BaseService
from src.services.rank_service.adapters import NewsPublicationAdapter, RedditPublicationAdapter, \
    GameLeaderboardPublicationAdapter
from src.services.shared_dependencies.calculators import NewsStatCalculator
from src.services.rank_service.filters import GameFilter, NewsFilter, DiscountFilter, RedditPostFilter, \
    RedditDevPostFilter, RedditMemeFilter, GameReviewFilter, LeaderboardFilter
from src.services.rank_service.rankers import NewsRanker, RedditDevPostRanker, RedditMemeRanker
from src.services.rank_service.rankers.ranker import GameRanker
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class RankEngineService(BaseService):

    def __init__(
        self, games_repo: GameRepository, game_snapshot_repo: GameSnapshotRepository,
        publish_repo: GamePublicationRepository,
        igdb_repo: IGDBRepository,       
        news_publication_repo: NewsPublicationRepository,
        leaderboard_publication_repo: GameLeaderboardPublicationRepository,
        discount_publication_repo: DiscountPublicationRepository,
        ranked_games_repo: RankedGameRepository,       
        reddit_post_repo: RedditPostRepository,
        ranked_reddit_posts_repo: RankedRedditPostRepository,       
        reddit_post_publication_repo: RedditPostPublicationRepository,       
        open_ai_client: AsyncOpenAI,   
        review_publication_repo: ReviewPublicationRepository,
        checked_entity_repo: CheckedEntityRepository,
        leaderboard_repo: LeaderboardRepository
    ) -> None:
        """The constructor of RankEngineService.
        :param games_repo: The game repository.
        :param game_snapshot_repo: The game snapshot repository.
        :param publish_repo: The game publication repository.
        :param igdb_repo: The IGDB repository.
        :param news_publication_repo: The news publication repository.
        :param leaderboard_publication_repo: The leaderboard publication repository.
        :param discount_publication_repo: The discount publication repository.
        :param ranked_games_repo: The ranked games repository.
        :param reddit_post_repo: The reddit post repository.
        :param ranked_reddit_posts_repo: The ranked reddit posts repository.
        :param reddit_post_publication_repo: The reddit post publication repository.
        :param open_ai_client: The OpenAI client.
        :param review_publication_repo: The review publication repository.
        :param checked_entity_repo: The checked entity repository.
        :param leaderboard_repo: The leaderboard repository.
        """
        super().__init__()
        self._log = get_logger().bind(service="rank_engine")
        self._games = games_repo
        self._game_snapshot_repo = game_snapshot_repo
        self._game_publication_repo = publish_repo
        self._igdb = igdb_repo
        self._ranker = GameRanker()
        self._filter = GameFilter()
        self._news_ranker = NewsRanker()
        self._news_filter = NewsFilter(open_ai_client, checked_entity_repo)
        self._leaderboard_filter = LeaderboardFilter()
        self._news_publication_repo = news_publication_repo
        self._discount_filter = DiscountFilter()
        self._discount_publication_repo = discount_publication_repo
        self._ranked_games_repo = ranked_games_repo
        self._news_stat_calculator = NewsStatCalculator()
        self._reddit_post_repo = reddit_post_repo
        self._leaderboard_repo = leaderboard_repo
        self._ranked_reddit_posts_repo = ranked_reddit_posts_repo
        self._leaderboard_publication_repo = leaderboard_publication_repo
        self._reddit_post_filter = RedditPostFilter(open_ai_client, checked_entity_repo)
        self._reddit_post_publication_repo = reddit_post_publication_repo
        self._reddit_dev_post_ranker = RedditDevPostRanker()
        self._reddit_dev_post_filter = RedditDevPostFilter(open_ai_client, checked_entity_repo)
        self._reddit_meme_ranker = RedditMemeRanker()
        self._reddit_meme_filter = RedditMemeFilter()
        self._game_review_filter = GameReviewFilter()
        self._review_publication_repo = review_publication_repo
        self._news_publication_adapter = NewsPublicationAdapter(
            open_ai_client=open_ai_client,
            news_publication_repo=news_publication_repo
        )
        self._reddit_publication_adapter = RedditPublicationAdapter(
            open_ai_client=open_ai_client,
            reddit_publication_repo=reddit_post_publication_repo
        )
        self._game_leaderboard_publication_adapter = GameLeaderboardPublicationAdapter(
            leaderboard_publication_repo=leaderboard_publication_repo
        )

    async def rank_all(self) -> None:
        """The main method serves to start ranking process for all entities"""
        cycle_log = self._log.bind(method="rank_all")
        cycle_log.info("ranking games and news")
        await self.rank_games()
        await self.rank_game_dev_story_reddit_posts(cycle_log)
        await self.rank_game_meme_reddit_posts(cycle_log)

    async def rank_games(self) -> None:
        """The main method for ranking games and another entities related to Steam games
        """
        cycle_log = self._log.bind(method="rank_games")
        cycle_log.info("cycle_start")
        last_ranked_at = await self._ranked_games_repo.get_max_value("last_ranked_at")
        last_ranked_at = last_ranked_at.get('max_value') or datetime.min
        # d) Scoring
        games = await self._games.get_all(
            {'updated_at': {'$gte': last_ranked_at}},
            sort_by={'updated_at': -1}, generator_mode=True, show_deleted=True
        )
        now = datetime.now()
        period_days = 45  # could be moved to settings
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
                if score < C.RANK_ENGINE_SERVICE_MIN_GAME_SCORE_TO_KEEP:
                    continue
                ranked_game = RankedGameSchema(
                    **game.model_dump(exclude={'created_at', 'updated_at'}),
                    last_score=score,
                    last_ranked_at=datetime.now()
                )

                self._rank_game_news(ranked_game, cycle_log)
                await self._ranked_games_repo.add_or_update(ranked_game, search_field="steam_appid")

            except Exception as e:
                cycle_log.error("rank_games", exc_info=True, error=e)

    async def filter_games(self, top_n: int) -> list[GamePublicationRecordSchema]:
        """The method filters games.
        :param top_n: The number of games to return.
        :return: The list of games.
        """
        cycle_log = self._log.bind(method="filter_games")
        cycle_log.info("started")
        now = datetime.now()
        params = {
            'last_score': {'$gte': C.GAME_FILTER_RATING_MIN},
            '$or': [
                {"release_date": {"$gte": now - timedelta(days=C.GAME_FILTER_RELEASE_DATE_DELTA_DAYS)}},
                {"release_date": None}
            ]
        }
        scored_games = await self._ranked_games_repo.get_all(
            params, sort_by={'last_score': -1}, generator_mode=True
        )

        unpublished = []
        async for game in scored_games:
            try:
                was = await self._game_publication_repo.was_published(game.steam_appid)
                if was:
                    continue
                meta = await self._igdb.get_one({'steam_appid': game.steam_appid})

                if self._filter.should_publish(game, meta, game.last_score):
                    rec = GamePublicationRecordSchema(**game.model_dump())
                    unpublished.append(rec)
                    if len(unpublished) >= top_n:
                        break
            except Exception as e:
                cycle_log.error("filter_games", exc_info=True, error=e)

        return unpublished

    def _rank_game_news(self, game: RankedGameModel | RankedGameSchema | GameModel, cycle_log: Logger) -> None:
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

    async def rank_game_dev_story_reddit_posts(self, cycle_log: Logger) -> None:
        """The method ranks game dev story reddit posts.
        :param cycle_log: The logger to use for logging.
        """
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
        """The method ranks game meme reddit posts.
        :param cycle_log: The logger object to use for logging.
        """
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
    
    async def filter_game_leaderboards(self, top_n: int) -> list[GameLeaderboardPublicationSchema]:
        """The method filters games leaderboards.
        :param top_n: The number of leaderboards to return.
        :return: The list of leaderboards.
        """
        cycle_log = self._log.bind(method="filter_games_leaderboards")
        cycle_log.info("started")        
        now = datetime.now()
        game_leaderboards = await self._leaderboard_repo.get_all(
            {'updated_at': {'$gte': now - timedelta(days=C.GAME_LEADERBOARD_FILTER_MAX_AGE_DAYS)}},
            generator_mode=True
        )
        unpublished = []
        async for leaderboard in game_leaderboards:
            try:
                scored_game = await self._ranked_games_repo.get_one(
                    {
                        'last_score': {'$gte': C.GAME_LEADERBOARD_FILTER_RATING_MIN},
                        'steam_appid': leaderboard.steam_appid
                    },
                )
                if not scored_game:
                    continue

                leaderboard_publication = GameLeaderboardPublicationSchema(
                    **leaderboard.model_dump(), game_name=scored_game.name
                )
                was = await self._game_leaderboard_publication_adapter.was_published(leaderboard_publication)
                if was:
                    continue

                if self._leaderboard_filter.should_publish(scored_game):
                    unpublished.append(leaderboard_publication)
                    if len(unpublished) >= top_n:
                        break
            except Exception as e:
                cycle_log.error("filter_games_leaderboards", exc_info=True, error=e)

        return unpublished
    
    async def filter_news(self, top_n: int) -> list[NewsPublicationSchema]:
        """The method filters gaming news.
        :param top_n: The number of news to return.
        :return: The list of news.
        """
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
        seen_news = set()
        async for game in scored_games:
            try:
                async for filtered in self._news_filter.filter_news(game.last_news[:1], game):
                    if filtered.gid in seen_news:
                        continue
                    seen_news.add(filtered.gid)
                    if not await self._news_publication_adapter.was_published(filtered):
                        unpublished.append(filtered)

                        if len(unpublished) >= top_n:
                            return unpublished

            except Exception as e:
                cycle_log.error(f"Error filtering news for game {game.steam_appid}: {e}")

        self._news_filter.clean()
        return unpublished

    async def filter_reviews(self, top_n: int) -> list[ReviewPublicationSchema]:
        """The method filters game reviews.
        :param top_n: The number of reviews to return.
        :return: The list of reviews.
        """
        cycle_log = self._log.bind(method="filter_reviews")
        cycle_log.info("started")
        now = datetime.now()
        scored_games = await self._ranked_games_repo.get_all(
            {
                'last_score': {'$gte': C.REVIEWS_FILTER_GAME_RATING_MIN},
                '$or': [
                    {"release_date": {"$gte": now - timedelta(days=C.REVIEWS_FILTER_GAME_RELEASE_DATE_DELTA_DAYS)}},
                    {"release_date": None}
                ]
            },
            sort_by={'last_score': -1}, generator_mode=True
        )
        unpublished = []
        async for game in scored_games:
            try:
                filtered = self._game_review_filter.filter_reviews(game)
                if not filtered:
                    continue

                if not await self._review_publication_repo.was_published(filtered.steam_appid):
                    unpublished.append(filtered)

                    if len(unpublished) >= top_n:
                        return unpublished

            except Exception as e:
                cycle_log.error(f"Error filtering reviews for game {game.steam_appid}: {e}")

        return unpublished

    async def filter_reddit_posts(self, top_n: int) -> list[RedditPostPublicationSchema]:
        """The method filters game-related reddit posts.
        :param top_n: The number of posts to return.
        :return: The list of posts.
        """
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
            try:
                reddit_posts = await self._ranked_reddit_posts_repo.get_all(
                    {'steam_appid': game.steam_appid}, limit=1, sort_by={'created_utc': -1}
                )
                async for filtered in self._reddit_post_filter.filter_posts(reddit_posts, game):
                    if not await self._reddit_publication_adapter.was_published(filtered):
                        unpublished.append(filtered)
                        if len(unpublished) >= top_n:
                            return unpublished

            except Exception as e:
                cycle_log.error(f"Error filtering reddit posts for game {game.steam_appid}: {e}")

        self._reddit_post_filter.clean()
        return unpublished

    async def filter_game_dev_reddit_posts(self, top_n: int) -> list[RedditPostPublicationSchema]:
        """The method filters reddit posts related to game development.
        :param top_n: The number of posts to return.
        :return: The list of posts.
        """
        cycle_log = self._log.bind(method="filter_reddit_posts")
        cycle_log.info("started")

        unpublished = []
        if top_n <= 0:
            return unpublished

        reddit_posts = await self._ranked_reddit_posts_repo.get_all(
            {'type': 'game_dev_story', 'last_score': {'$gte': C.REDDIT_GAME_DEV_FILTER_RATING_MIN}},
            sort_by={'last_score': -1}
        )
        seen_posts = set()
        async for post in self._reddit_dev_post_filter.filter_posts(reddit_posts):
            try:
                if post.reddit_id in seen_posts:
                    continue
                seen_posts.add(post.reddit_id)
                if not await self._reddit_publication_adapter.was_published(post):
                    unpublished.append(post)
                    if len(unpublished) >= top_n:
                        return unpublished

            except Exception as e:
                cycle_log.error(f"Error filtering game dev reddit posts {post.reddit_id}: {e}")
        self._reddit_dev_post_filter.clean()
        return unpublished

    async def filter_game_meme_reddit_posts(self, top_n: int) -> list[RedditPostPublicationSchema]:
        """The method filters reddit posts related to game memes.
        :param top_n: The number of posts to return.
        :return: The list of posts.
        """
        cycle_log = self._log.bind(method="filter_game_meme_reddit_posts")
        cycle_log.info("started")

        unpublished = []
        if top_n <= 0:
            return unpublished

        reddit_posts = await self._ranked_reddit_posts_repo.get_all(
            {'type': 'meme', 'last_score': {'$gte': C.REDDIT_MEME_FILTER_MIN_SCORE}},
            sort_by={'last_score': -1}, generator_mode=True
        )
        added = set()
        async for post in reddit_posts:
            try:
                was = await self._reddit_post_publication_repo.was_published(post)
                if was:
                    continue

                checked_posts = self._reddit_meme_filter.filter_posts([post])
                for filtered in checked_posts:
                    if filtered.reddit_id in added:
                        continue

                    added.add(filtered.reddit_id)
                    unpublished.append(filtered)

                    if len(unpublished) >= top_n:
                        return unpublished

            except Exception as e:
                cycle_log.error(f"Error filtering game meme reddit post {post.reddit_id}: {e}")

        return unpublished

    async def filter_discounts(self, top_n: int) -> list[DiscountPublicationSchema]:
        """The method filters discounts.
        :param top_n: The number of discounts to return.
        :return: The list of discounts.
        """
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
                snapshots = await self._game_snapshot_repo.get_all(
                    {
                        "steam_appid": game.steam_appid,
                        "snapshot_time": {"$gte": now - timedelta(days=C.DISCOUNT_FILTER_DAYS_LIMIT)}
                    },
                    sort_by={'snapshot_time': -1}
                )
                discount = self._discount_filter.detect_discount(game, snapshots)
                if discount:
                    was = await self._discount_publication_repo.was_published(discount)
                    if not was:
                        unpublished.append(discount)

                if len(unpublished) >= top_n:
                    break

            except Exception as e:
                cycle_log.error("filter_discounts", exc_info=True, error=e)

        return unpublished
