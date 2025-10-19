from typing import Optional
from src.config import constants as C
from src.config.settings import settings
from src.db.repositories import GameRepository, GameSnapshotRepository, PublicationRepository, IGDBRepository
from src.models import IGDBMeta
from src.models.game import GameModel
from src.schemas import PublicationRecordSchema
from src.services.base_service import BaseService
from src.services.rank_service.filters.filter import GameFilter
from src.services.rank_service.rankers.ranker import GameRanker
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class RankEngineService(BaseService):

    def __init__(
        self, games_repo: GameRepository, game_snapshot_repo: GameSnapshotRepository,
        publish_repo: PublicationRepository,
        igdb_repo: IGDBRepository,
        game_ranker: GameRanker,
        game_filter: GameFilter,
    ):
        super().__init__()
        self._log = get_logger().bind(service="rank_engine")
        self._games = games_repo
        self._game_snapshot_repo = game_snapshot_repo
        self._publish_repo = publish_repo
        self._igdb = igdb_repo
        self._ranker = game_ranker
        self._filter = game_filter


    async def rank_all(self, top_n: Optional[int] = None, candidates_limit: int = C.ORCH_CANDIDATES_LIMIT_DEFAULT):

        top_n = top_n or settings.TOP_N_TO_PUBLISH
        cycle_log = self._log.bind(top_n=top_n, candidates_limit=candidates_limit)
        cycle_log.info("cycle_start")

        # d) Скоринг
        games = await self._games.get_all(sort_by={'updated_at': -1}, limit=500)
        appids = [g.steam_appid for g in games]
        metas = await self._igdb.get_all({"steam_appid": {"$in": appids}}, sort_by={'updated_at': -1}, limit=500)
        metas = {meta.steam_appid: meta for meta in metas}
        scored: list[tuple[GameModel, Optional[IGDBMeta], float]] = []

        async def score_game(g: GameModel):
            meta = metas.get(g.steam_appid)
            score = await self._ranker.evaluate(g, meta)
            await self._games.update_score(g.steam_appid, score)
            scored.append((g, meta, score))

        await self._bounded_gather(score_game, games, concurrency=C.ORCH_SCORE_CONCURRENCY)

        # e) Фильтр + топ-N среди непубликованных
        filtered = [x for x in scored if self._filter.should_publish(x[0], x[1], x[2])]
        filtered.sort(key=lambda t: t[2], reverse=True)

        unpublished = []
        for g, m, s in filtered:
            was = await self._publish_repo.was_published(g.steam_appid)
            if not was:
                rec = PublicationRecordSchema(steam_appid=g.steam_appid, score_at_publish=s)
                unpublished.append(rec)
            if len(unpublished) >= top_n:
                break

        await self._publish_repo.add_or_update(unpublished, search_field="steam_appid")
