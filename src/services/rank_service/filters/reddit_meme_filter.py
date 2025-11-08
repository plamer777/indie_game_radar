# src/services/rank_service/filters/reddit_meme_filter.py
from datetime import datetime, timedelta
from src.models import RankedRedditPost
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class RedditMemeFilter:
    """
    Фильтр для отбора качественных игровых мемов.
    Проверяет только возраст и ранк-оценку.
    """

    def __init__(self, max_age_days: int = C.REDDIT_MEME_FILTER_MAX_AGE_DAYS, min_rank_score: float = C.REDDIT_MEME_FILTER_MIN_SCORE):
        self.max_age = timedelta(days=max_age_days)
        self.min_rank = min_rank_score

    def filter_posts(self, posts: list[RankedRedditPost]) -> list[RankedRedditPost]:
        """
        Возвращает список мемов, прошедших базовую фильтрацию.
        """
        now = datetime.now()
        result = []

        for p in posts:
            if not p.created_utc:
                continue

            age = now - p.created_utc
            if age > self.max_age:
                continue
            if p.last_score < self.min_rank:
                continue

            result.append(p)

        # сортировка по рейтингу, свежие — первыми
        result.sort(key=lambda x: (x.last_score, x.created_utc), reverse=True)
        return result
