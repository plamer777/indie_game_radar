from __future__ import annotations
import asyncio
from src.clients import SpeedrunClient
from src.container import orchestrator
from src.models.speedrun import Category, Result, Player, CategoryLeader, GameLeaderboard
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


async def app_main() -> None:
    """The main application function."""
    log = get_logger().bind(app="igr")
    log.info("app_start")
    # await orchestrator.start()
    log.info("app_stop")

    speedrun = SpeedrunClient()
    game_id = await speedrun.search_game_id("terraria")
    game_info = await speedrun.get_game_info(game_id)
    leaders = await speedrun.get_world_records(
        game_id, top=5, scope='full-game', miscellaneous=False
    )
    game_leaderboard = GameLeaderboard(**game_info)

    for leader in leaders:
        category_id = leader.get('category')
        leader_run = leader.get('runs', [])[0] if leader.get('runs', []) else {}
        place = leader_run.get('place')
        leader_run = leader_run.get('run', {})
        player = leader_run.get('players', [])[0] if leader_run.get('players', []) else {}
        player_info = await speedrun.get_player_info(player.get('id'))
        player_info = Player(**player_info)
        result = Result(**leader_run, player=player_info, place=place)
        category = await speedrun.get_category(category_id)
        category = Category(**category)
        category_leader = CategoryLeader(weblink=leader.get('weblink'), category=category, result=result)
        game_leaderboard.category_leaderboards.append(category_leader)


if __name__ == "__main__":
    asyncio.run(app_main())
