from typing import Optional
from src.clients import SpeedrunClient
from src.models.speedrun import Player, Result, Category, CategoryLeader
from src.schemas import GameLeaderboardSchema
# ---------------------------------------------------------------------------------------------------------------------


class SpeedrunAdapter:
    """The adapter class for Speedrun.com API"""

    def __init__(self, speedrun_client: SpeedrunClient) -> None:
        """The constructor method for SpeedrunAdapter class.
        :param speedrun_client: an instance of SpeedrunClient class
        """
        self._speedrun_client = speedrun_client

    async def fetch_leaderboard(self, game_name: str) -> Optional[GameLeaderboardSchema]:
        """The method serves to fetch leaderboard for a game
        :param game_name: a string representing the name of game to fetch leaderboard for
        :return: an instance of GameLeaderboardSchema class or None if game was not found
        """
        game_id = await self._speedrun_client.search_game_id(game_name)

        if not game_id:
            return None

        game_info = await self._speedrun_client.get_game_info(game_id)
        leaders = await self._speedrun_client.get_world_records(
            game_id, top=5, scope='full-game', miscellaneous=False
        )
        game_leaderboard = GameLeaderboardSchema(**game_info)

        for leader in leaders:
            category_id = leader.get('category')
            leader_run = leader.get('runs', [])[0] if leader.get('runs', []) else {}
            place = leader_run.get('place')
            leader_run = leader_run.get('run', {})
            player = leader_run.get('players', [])[0] if leader_run.get('players', []) else {}
            player_info = await self._speedrun_client.get_player_info(player.get('id'))
            player_info = Player(**player_info)
            result = Result(**leader_run, player=player_info, place=place)
            category = await self._speedrun_client.get_category(category_id)
            category = Category(**category)
            category_leader = CategoryLeader(weblink=leader.get('weblink'), category=category, result=result)
            game_leaderboard.category_leaderboards.append(category_leader)

        return game_leaderboard
