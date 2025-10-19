from src.clients.igdb_client import AsyncIGDBClient
from src.clients.steam_client import AsyncSteamClient
from src.clients.telegram_client import TelegramPublisher
from src.db.repositories import GameRepository, IGDBRepository, PublicationRepository, AppRepository, \
    GameSnapshotRepository
from src.managers.cache import RedisCache
from src.orchestrators.core_orchestrator import Orchestrator
from src.services.data_service import APIHarvesterService
from src.services.publisher_service import PublisherService
from src.services.rank_service.filters.filter import GameFilter
from src.services.rank_service.rank_engine_service import RankEngineService
from src.services.rank_service.rankers.ranker import GameRanker
# ---------------------------------------------------------------------------------------------------------------------

# Managers
cache = RedisCache()

# Clients/services
steam = AsyncSteamClient(cache)
igdb = AsyncIGDBClient(cache)
tg = TelegramPublisher()
ranker = GameRanker()
gfilter = GameFilter()

# Repositories
games_repo = GameRepository()
igdb_repo = IGDBRepository()
pub_repo = PublicationRepository()
app_repo = AppRepository()
game_snapshot_repo = GameSnapshotRepository()

# Services
api_harvester = APIHarvesterService(
    steam_client=steam,
    igdb_client=igdb,
    game_repo=games_repo,
    game_snapshot_repo=game_snapshot_repo,
    app_repo=app_repo,
    igdb_repo=igdb_repo,
)

rank_engine = RankEngineService(
    games_repo=games_repo,
    game_snapshot_repo=game_snapshot_repo,
    publish_repo=pub_repo,
    igdb_repo=igdb_repo,
    game_ranker=ranker,
    game_filter=gfilter
)

publisher = PublisherService(
    publication_repo=pub_repo,
    publisher=tg,
    game_repo=games_repo,
    igdb_repo=igdb_repo,
)


orchestrator = Orchestrator(

)