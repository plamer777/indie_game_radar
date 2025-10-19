from typing import Optional
from src.config import constants as C
from src.clients.igdb_client import AsyncIGDBClient
from src.clients.steam_client import AsyncSteamClient
from src.db.repositories import GameRepository, GameSnapshotRepository, AppRepository, IGDBRepository
from src.models.game import GameModel
from src.schemas import GameSnapshotSchema, GameSchema
from src.schemas.igdb_schemas import IGDBMetaSchema
from src.services.base_service import BaseService
from src.utils.logging import get_logger
# --------------------------------------------------------------------------------------------------------------------


class APIHarvesterService(BaseService):
    def __init__(
        self,
        steam_client: AsyncSteamClient,
        igdb_client: AsyncIGDBClient,
        game_repo: GameRepository,
        game_snapshot_repo: GameSnapshotRepository,
        app_repo: AppRepository,
        igdb_repo: IGDBRepository,
    ):
        self._steam = steam_client
        self._igdb_client = igdb_client
        self._games = game_repo
        self._game_snapshot_repo = game_snapshot_repo
        self._app_repo = app_repo
        self._igdb = igdb_repo
        self._log = get_logger().bind(service="api_harvester")

    async def fetch_steam_apps(self):
        last_mofied = await self._app_repo.get_max_value("last_modified")
        last_mofied = last_mofied.get('max_value')
        async for app_batch in self._steam.fetch_apps(since=last_mofied):
            await self._app_repo.add_or_update(app_batch, search_field="appid")

    async def fetch_steam_games(self):
        apps = await self._app_repo.get_all(sort_by={'last_modified': -1}, limit=500, generator_mode=True)
        fetched_games = []
        for app in apps:
            game = await self._steam.fetch_full_app_details(app.appid)
            if game:
                fetched_games.append(game)
                changed = await self._games.add_or_update(game, search_field="steam_appid")
                if changed:
                    total_achievements = len(game.ext_info.achievements or [])
                    avg_unlock_percent = (
                        sum(a.percent for a in game.ext_info.achievements or []) / total_achievements
                        if total_achievements else None
                    )
                    snapshot = GameSnapshotSchema(
                        steam_appid=game.steam_appid,
                        price=game.price.final if game.price else None,
                        discount_percent=game.price.discount_percent if game.price else None,
                        current_players=game.ext_info.current_players,
                        total_achievements=total_achievements,
                        avg_unlock_percent=avg_unlock_percent,
                        review_ratio=game.ext_info.review_summary.ratio if game.ext_info.review_summary else 0,
                        avg_days_per_news=game.ext_info.news_stats.avg_interval_days
                    )
                    await self._game_snapshot_repo.add_new(snapshot.model_dump(mode="json"))

                if len(fetched_games) >= 50:
                    await self._bounded_gather(
                        self.fetch_meta_by_game, fetched_games, concurrency=C.ORCH_FETCH_META_CONCURRENCY
                    )
                    fetched_games.clear()

        await self._bounded_gather(
            self.fetch_meta_by_game, fetched_games, concurrency=C.ORCH_FETCH_META_CONCURRENCY
        )

    async def fetch_igdb_metas(self) -> None:
        """The method fetches IGDB meta for games and stores them in the database.
        """
        cycle_log = self._log.bind(service="fetch_igdb_metas")
        cycle_log.info("cycle_start")
        try:

            games = await self._games.get_all(sort_by={'updated_at': -1}, limit=500)
            await self._bounded_gather(self.fetch_meta_by_game, games, concurrency=C.ORCH_FETCH_META_CONCURRENCY)
        except Exception as e:
            cycle_log.error("cycle_error", exc_info=True, error=e)

    async def fetch_meta_by_game(self, game: GameSchema | GameModel) -> Optional[IGDBMetaSchema]:
        meta = await self._igdb_client.fetch_game_meta(name=game.name, steam_appid=game.steam_appid)
        if meta:
            meta.steam_appid = game.steam_appid
            await self._igdb.add_or_update(meta, search_field="steam_appid")

        return meta

    async def fetch_all(self):
        # a) Получаем список appids (будет очень большим). Ограничим первыми N для демо.
        cycle_log = self._log.bind(service="save_to_db")
        cycle_log.info("cycle_start")
        try:
            await self.fetch_steam_apps()

            # b) Детали Steam
            await self.fetch_steam_games()

            # c) IGDB meta
            await self.fetch_igdb_metas()
        except Exception as e:
            cycle_log.error("cycle_error", exc_info=True, error=e)

