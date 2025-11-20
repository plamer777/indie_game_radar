from src.models import RankedGameModel
from src.services.rank_service.filters.base_filter import BaseFilter
# ---------------------------------------------------------------------------------------------------------------------


class LeaderboardFilter(BaseFilter):
    """
    The filter for leaderboards of games.
    """

    def __init__(self) -> None:
        """
        The constructor of LeaderboardFilter.
        """
        super().__init__()

    def should_publish(self, game: RankedGameModel) -> bool:
        """
        The method checks if the game to publish related leaderboards.
        :param game: The game to check.
        :return: True if the game should be published, False otherwise.
        """
        if not self._is_indie_game(game):
            return False

        return True
