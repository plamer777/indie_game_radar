from __future__ import annotations
import asyncio

from src.clients import SpeedrunComClient
from src.container import orchestrator
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


async def app_main() -> None:
    """The main application function."""
    log = get_logger().bind(app="igr")
    log.info("app_start")
    # await orchestrator.start()
    log.info("app_stop")
    speedrun = SpeedrunComClient()
    game_id = await speedrun.search_game_id("terraria")
    game = await speedrun.get_world_records(game_id)
    log.info(f"game: {game}")


if __name__ == "__main__":
    asyncio.run(app_main())
