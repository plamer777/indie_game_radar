from __future__ import annotations
import asyncio
from typing import Optional, Sequence
from schemas import GameSchema, GameSnapshotSchema
from schemas.igdb_schemas import IGDBMetaSchema
from utils.logging import get_logger
from config.settings import settings
from clients.steam_client import AsyncSteamClient
from clients.igdb_client import AsyncIGDBClient
from clients.telegram_client import TelegramPublisher
from services.ranker import GameRanker
from services.filter import GameFilter
from db.repositories.repositories import GameRepository, IGDBRepository, PublicationRepository, AppRepository, \
    GameSnapshotRepository
from models.game import GameModel
from models.igdb import IGDBMeta
from models.publication import PublicationRecord
from config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class Orchestrator:
    def __init__(
        self,
        games_repo: GameRepository,
        igdb_repo: IGDBRepository,
        pub_repo: PublicationRepository,
        game_snapshot_repo: GameSnapshotRepository,
        steam: AsyncSteamClient,
        igdb: AsyncIGDBClient,
        publisher: TelegramPublisher,
        ranker: GameRanker,
        game_filter: GameFilter,
        app_repo: AppRepository,
    ) -> None:
        self._games = games_repo
        self._igdb = igdb_repo
        self._pub = pub_repo
        self._steam = steam
        self._igdb_client = igdb
        self._publisher = publisher
        self._ranker = ranker
        self._filter = game_filter
        self._app_repo = app_repo
        self._game_snapshot_repo = game_snapshot_repo
        self._log = get_logger().bind(service="orchestrator")

    async def save_to_db(self):
        # a) Получаем список appids (будет очень большим). Ограничим первыми N для демо.
        cycle_log = self._log.bind(service="save_to_db")
        cycle_log.info("cycle_start")
        # last_mofied = await self._app_repo.get_max_value("last_modified")
        # last_mofied = last_mofied.get('max_value')
        # async for app_batch in self._steam.fetch_apps(since=last_mofied):
        #     await self._app_repo.add_or_update(app_batch, search_field="appid")

        # b) Детали Steam
        async def fetch_game(appid: int):
            game = await self._steam.fetch_full_app_details(appid)
            if game:
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


        apps = await self._app_repo.get_all(sort_by={'last_modified': -1}, limit=500)
        appids = [app.appid for app in apps]
        for appid in appids:
            await fetch_game(appid)

        # await _bounded_gather(fetch_game, appids, concurrency=C.ORCH_FETCH_GAME_CONCURRENCY)

        games = await self._games.get_all(sort_by={'updated_at': -1}, limit=500)
        if not games:
            cycle_log.warning("no_games_fetched")
            return

        # c) IGDB meta для каждого (по имени)
        metas: dict[int, IGDBMetaSchema] = {}
        #
        async def fetch_meta(g: GameSchema | GameModel):
            meta = await self._igdb_client.fetch_game_meta(name=g.name, steam_appid=g.steam_appid)
            if meta:
                meta.steam_appid = g.steam_appid
                metas[g.steam_appid] = meta
                await self._igdb.add_or_update(meta, search_field="steam_appid")

        for game in games:
            await fetch_meta(game)
        # await _bounded_gather(fetch_meta, games, concurrency=C.ORCH_FETCH_META_CONCURRENCY)

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
            # scored.append((g, meta, score))
        for g in games:
            await score_game(g)
        # await _bounded_gather(score_game, games, concurrency=C.ORCH_SCORE_CONCURRENCY)


    async def run_cycle(self, top_n: Optional[int] = None, candidates_limit: int = C.ORCH_CANDIDATES_LIMIT_DEFAULT) -> None:
        top_n = top_n or settings.TOP_N_TO_PUBLISH
        cycle_log = self._log.bind(top_n=top_n, candidates_limit=candidates_limit)
        cycle_log.info("cycle_start")

        # e) Фильтр + топ-N среди непубликованных
        filtered = [x for x in scored if self._filter.should_publish(x[0], x[1], x[2])]
        filtered.sort(key=lambda t: t[2], reverse=True)

        unpublished = []
        for g, m, s in filtered:
            was = await self._pub.was_published(g.steam_appid)
            if not was:
                unpublished.append((g, m, s))
            if len(unpublished) >= top_n:
                break

        # f) Публикации
        for g, m, s in unpublished:
            rec = PublicationRecord(steam_appid=g.steam_appid, score_at_publish=s)
            msg_id = await self._publisher.publish(g, m, s)
            if msg_id:
                rec.message_id = msg_id
                await self._pub.mark_published(rec)
            else:
                await self._pub.mark_failed(rec, error="publish_failed")

        cycle_log.info("cycle_end", published=len(unpublished), candidates=len(games))


async def _bounded_gather(func, iterable: Sequence, concurrency: int = 10):
    sem = asyncio.Semaphore(concurrency)

    async def worker(item):
        async with sem:
            return await func(item)

    await asyncio.gather(*(worker(i) for i in iterable))
