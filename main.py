from __future__ import annotations
import asyncio
from src.container import orchestrator
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


async def app_main() -> None:
    log = get_logger().bind(app="igr")
    log.info("app_start")

    await orchestrator.start()

    log.info("app_stop")


if __name__ == "__main__":
    asyncio.run(app_main())
