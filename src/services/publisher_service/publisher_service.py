from src.clients.telegram_client import TelegramPublisher
from src.db.repositories import PublicationRepository, GameRepository, IGDBRepository
from src.models.publication import PublishStatus
from src.services.base_service import BaseService
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class PublisherService(BaseService):

    def __init__(
        self, publication_repo: PublicationRepository, publisher: TelegramPublisher,
        game_repo: GameRepository, igdb_repo: IGDBRepository
    ):
        self._publication_repo = publication_repo
        self._publisher = publisher
        self._games = game_repo
        self._igdb = igdb_repo
        self._log = get_logger().bind(service="PublisherService")

    async def publish_all(self):
        cycle_log = self._log.bind(service="publish_all")
        cycle_log.info("cycle_start")
        publications = await self._publication_repo.get_all({'status': PublishStatus.pending})
        app_ids = [pub.steam_appid for pub in publications]
        games = await self._games.get_all({'steam_appid': {'$in': app_ids}})
        metas = await self._igdb.get_all({'steam_appid': {'$in': app_ids}})
        games = {game.steam_appid: game for game in games}
        metas = {meta.steam_appid: meta for meta in metas}

        for item in publications:
            game = games.get(item.steam_appid)
            meta = metas.get(item.steam_appid)
            msg_id = await self._publisher.publish(game, meta, item.score_at_publish)
            if msg_id:
                item.message_id = msg_id
                await self._publication_repo.mark_published(item)
            else:
                await self._publication_repo.mark_failed(item, error="publish_failed")

        cycle_log.info("cycle_end", published=len(publications))