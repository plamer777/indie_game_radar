from __future__ import annotations
from typing import Optional
from src.services.data_service import APIHarvesterService
from src.services.publisher_service import PublisherService
from src.services.rank_service.rank_engine_service import RankEngineService
from src.utils.logging import get_logger
from src.config.settings import settings
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class Orchestrator:
    def __init__(
        self,
        api_harvester: APIHarvesterService,
        rank_engine: RankEngineService,
        publisher: PublisherService,
    ) -> None:
        self._api_harvester = api_harvester
        self._rank_engine = rank_engine
        self._publisher = publisher
        self._log = get_logger().bind(service="orchestrator")

    async def save_to_db(self):
        # a) Получаем список appids (будет очень большим). Ограничим первыми N для демо.
        cycle_log = self._log.bind(service="save_to_db")
        cycle_log.info("cycle_start")
        await self._api_harvester.fetch_all()


    async def run_cycle(
        self, top_n: Optional[int] = None, candidates_limit: int = C.ORCH_CANDIDATES_LIMIT_DEFAULT
    ) -> None:
        top_n = top_n or settings.TOP_N_TO_PUBLISH
        cycle_log = self._log.bind(top_n=top_n, candidates_limit=candidates_limit)
        cycle_log.info("cycle_start")

        await self._rank_engine.rank_all()

        # f) Публикации
        await self._publisher.publish_all()

