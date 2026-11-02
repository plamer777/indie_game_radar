from openai import AsyncOpenAI
from src.clients import SpeedrunClient, DirectRedditClient
from src.clients.igdb_client import AsyncIGDBClient
from src.clients.steam_client import AsyncSteamClient
from src.clients.telegram_client import TelegramPublisher
from src.clients.tumblr_client import TumblrClient
from src.config import constants as C
from src.config.settings import settings
from src.db.repositories import GameRepository, IGDBRepository, GamePublicationRepository, AppRepository, \
    GameSnapshotRepository, NewsPublicationRepository, DiscountPublicationRepository, RankedGameRepository, \
    RedditPostRepository, RankedRedditPostRepository, RedditPostPublicationRepository, CheckedEntityRepository, \
    ReviewPublicationRepository, LeaderboardRepository, GameLeaderboardPublicationRepository
from src.orchestrators.core_orchestrator import Orchestrator
from src.services.data_service import APIHarvesterService
from src.services.publisher_service import PublisherService
from src.services.rank_service.rank_engine_service import RankEngineService
# ---------------------------------------------------------------------------------------------------------------------

# Managers
client = AsyncOpenAI(api_key=settings.OPEN_AI_KEY)

# Repositories
games_repo = GameRepository()
leaderboard_repo = LeaderboardRepository()
ranked_games_repo = RankedGameRepository()
igdb_repo = IGDBRepository()
pub_repo = GamePublicationRepository()
app_repo = AppRepository()
game_snapshot_repo = GameSnapshotRepository()
news_pub_repo = NewsPublicationRepository()
discount_pub_repo = DiscountPublicationRepository()
reddit_post_repo = RedditPostRepository()
ranked_reddit_posts_repo = RankedRedditPostRepository()
reddit_post_publication_repo = RedditPostPublicationRepository()
checked_entity_repo = CheckedEntityRepository()
review_publication_repo = ReviewPublicationRepository()
leaderboard_publication_repo = GameLeaderboardPublicationRepository()


# Clients/helpers
steam = AsyncSteamClient()
igdb = AsyncIGDBClient()
reddit = DirectRedditClient()
speedrun_client = SpeedrunClient()
tg = TelegramPublisher()

# Tumblr client (optional - only instantiate if credentials are provided)
tumblr = None
if all([C.TUMBLR_CONSUMER_KEY, C.TUMBLR_CONSUMER_SECRET, C.TUMBLR_OAUTH_TOKEN, C.TUMBLR_OAUTH_TOKEN_SECRET, C.TUMBLR_BLOG_IDENTIFIER]):
    tumblr = TumblrClient(
        consumer_key=C.TUMBLR_CONSUMER_KEY,
        consumer_secret=C.TUMBLR_CONSUMER_SECRET,
        oauth_token=C.TUMBLR_OAUTH_TOKEN,
        oauth_token_secret=C.TUMBLR_OAUTH_TOKEN_SECRET,
        blog_identifier=C.TUMBLR_BLOG_IDENTIFIER
    )

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
    speedrun_client=speedrun_client,
    leaderboard_repo=leaderboard_repo,
    ranked_games_repo=ranked_games_repo,
)

rank_engine = RankEngineService(
    games_repo=games_repo,
    game_snapshot_repo=game_snapshot_repo,
    publish_repo=pub_repo,
    igdb_repo=igdb_repo,
    news_publication_repo=news_pub_repo,
    discount_publication_repo=discount_pub_repo,
    ranked_games_repo=ranked_games_repo,
    reddit_post_repo=reddit_post_repo,
    ranked_reddit_posts_repo=ranked_reddit_posts_repo,
    reddit_post_publication_repo=reddit_post_publication_repo,
    open_ai_client=client,
    review_publication_repo=review_publication_repo,
    checked_entity_repo=checked_entity_repo,
    leaderboard_publication_repo=leaderboard_publication_repo,
    leaderboard_repo=leaderboard_repo
)

publisher = PublisherService(
    publication_repo=pub_repo,
    publisher=tg,
    discount_publication_repo=discount_pub_repo,
    news_publication_repo=news_pub_repo,
    reddit_post_publication_repo=reddit_post_publication_repo,
    open_ai_client=client,
    review_publication_repo=review_publication_repo,
    leaderboard_publication_repo=leaderboard_publication_repo,
    tumblr_client=tumblr,
)


orchestrator = Orchestrator(
    api_harvester=api_harvester,
    rank_engine=rank_engine,
    publisher=publisher
)
