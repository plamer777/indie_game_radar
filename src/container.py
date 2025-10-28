from openai import OpenAI

from src.clients import RedditClient
from src.clients.igdb_client import AsyncIGDBClient
from src.clients.steam_client import AsyncSteamClient
from src.clients.telegram_client import TelegramPublisher
from src.config.settings import settings
from src.db.repositories import GameRepository, IGDBRepository, GamePublicationRepository, AppRepository, \
    GameSnapshotRepository, NewsPublicationRepository, DiscountPublicationRepository, RankedGameRepository, \
    RedditPostRepository, RankedRedditPostRepository
from src.managers.cache import RedisCache
from src.orchestrators.core_orchestrator import Orchestrator
from src.scheduler.scheduler import AsyncScheduler
from src.services.data_service import APIHarvesterService
from src.services.publisher_service import PublisherService
from src.services.rank_service.filters import DiscountFilter
from src.services.rank_service.filters.filter import GameFilter
from src.services.rank_service.filters.news_filter import NewsFilter
from src.services.rank_service.rank_engine_service import RankEngineService
from src.services.rank_service.rankers import NewsRanker, RedditPostRanker
from src.services.rank_service.rankers.ranker import GameRanker
# ---------------------------------------------------------------------------------------------------------------------

# Managers
cache = RedisCache()
client = OpenAI(api_key=settings.OPEN_AI_KEY)

# Schedulers
scheduler = AsyncScheduler()

# Clients/helpers
steam = AsyncSteamClient(cache)
igdb = AsyncIGDBClient(cache)
reddit = RedditClient()
tg = TelegramPublisher()
ranker = GameRanker()
gfilter = GameFilter()
news_ranker = NewsRanker()
news_filter = NewsFilter(client)
discount_filter = DiscountFilter()
reddit_post_ranker = RedditPostRanker()


# Repositories
games_repo = GameRepository()
ranked_games_repo = RankedGameRepository()
igdb_repo = IGDBRepository()
pub_repo = GamePublicationRepository()
app_repo = AppRepository()
game_snapshot_repo = GameSnapshotRepository()
news_pub_repo = NewsPublicationRepository()
discount_pub_repo = DiscountPublicationRepository()
reddit_post_repo = RedditPostRepository()
ranked_reddit_posts_repo = RankedRedditPostRepository()

# Services
api_harvester = APIHarvesterService(
    steam_client=steam,
    igdb_client=igdb,
    reddit_client=reddit,
    game_repo=games_repo,
    game_snapshot_repo=game_snapshot_repo,
    app_repo=app_repo,
    igdb_repo=igdb_repo,
    reddit_post_repo=reddit_post_repo,
)

rank_engine = RankEngineService(
    games_repo=games_repo,
    game_snapshot_repo=game_snapshot_repo,
    publish_repo=pub_repo,
    igdb_repo=igdb_repo,
    game_ranker=ranker,
    game_filter=gfilter,
    news_ranker=news_ranker,
    news_filter=news_filter,
    news_publication_repo=news_pub_repo,
    discount_publication_repo=discount_pub_repo,
    discount_filter=discount_filter,
    ranked_games_repo=ranked_games_repo,
    reddit_post_ranker=reddit_post_ranker,
    reddit_post_repo=reddit_post_repo,
    ranked_reddit_posts_repo=ranked_reddit_posts_repo,
)

publisher = PublisherService(
    publication_repo=pub_repo,
    publisher=tg,
    game_repo=games_repo,
    igdb_repo=igdb_repo,
)


orchestrator = Orchestrator(
    api_harvester=api_harvester,
    rank_engine=rank_engine,
    publisher=publisher,
    scheduler=scheduler
)
