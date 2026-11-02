import random
from src.models import RankedGameModel
from src.schemas import ReviewPublicationSchema
from src.services.rank_service.filters.base_filter import BaseFilter
# ---------------------------------------------------------------------------------------------------------------------


class GameReviewFilter(BaseFilter):
    """
    Filter for selecting reviews.
    Takes a list of reviews and returns N randomly selected ones.
    """

    def __init__(self, sample_size: int = 10) -> None:
        """
        :param sample_size: how many reviews to return after sampling
        """
        super().__init__()
        self._sample_size = sample_size

    def filter_reviews(self, game: RankedGameModel) -> ReviewPublicationSchema | None:
        """
        Returns sample_size reviews randomly picked from the list.
        If there are fewer — returns all of them.
        """
        if not self._is_indie_game(game):
            return None
        review_info = game.ext_info.review_summary
        reviews = review_info.reviews
        if not reviews:
            return None

        # safe sample when there are fewer reviews than sample_size
        selected = random.sample(reviews, k=min(self._sample_size, len(reviews)))
        publication_schema = ReviewPublicationSchema(
            **review_info.model_dump(), steam_appid=game.steam_appid, game_name=game.name,
            image=game.header_image
        )
        publication_schema.reviews = selected

        return publication_schema
