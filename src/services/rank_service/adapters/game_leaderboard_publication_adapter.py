import hashlib
import json
from src.db.repositories import GameLeaderboardPublicationRepository
from src.models import GameLeaderboard
from src.schemas import GameLeaderboardPublicationSchema
# ---------------------------------------------------------------------------------------------------------------------


class GameLeaderboardPublicationAdapter:
    """The adapter for game leaderboard publication, used to mark game leaderboards as published or failed and check
    if they were published"""

    def __init__(self, leaderboard_publication_repo: GameLeaderboardPublicationRepository) -> None:
        """The constructor of GameLeaderboardPublicationAdapter.
        :param leaderboard_publication_repo: The leaderboard publication repository.
        """
        self._leaderboard_publication_repo = leaderboard_publication_repo

    def _calc_leaders_hash(self, record: GameLeaderboardPublicationSchema | GameLeaderboard) -> str:
        """Calculates the hash of the leaders in the leaderboard publication record.
        :param record: The leaderboard publication record.
        :return: The hash of the leaders.
        """
        leaders = []

        for c in record.category_leaderboards:
            # if order matters — do NOT sort
            leaders.append(c.result.player.id)

        data = json.dumps(leaders, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    async def mark_published(self, record: GameLeaderboardPublicationSchema) -> None:
        """The method marks the leaderboard as published.
        :param record: The leaderboard publication record.
        """
        record.leaders_hash = self._calc_leaders_hash(record)
        await self._leaderboard_publication_repo.mark_published(record)

    async def mark_failed(
        self, record: GameLeaderboardPublicationSchema, error: str
    ) -> None:
        """The method marks the leaderboard as failed.
        :param record: The leaderboard publication record.
        :param error: The error message.
        """
        record.leaders_hash = self._calc_leaders_hash(record)
        await self._leaderboard_publication_repo.mark_failed(record, error)

    async def was_published(
        self, record: GameLeaderboardPublicationSchema, channel: str = "telegram"
    ) -> bool:
        """The method checks if the leaderboard was published.
        :param record: The leaderboard publication record.
        :param channel: The channel to check for.
        :return: True if the leaderboard was published, False otherwise.
        """
        record.leaders_hash = self._calc_leaders_hash(record)
        return await self._leaderboard_publication_repo.was_published(record, channel)
