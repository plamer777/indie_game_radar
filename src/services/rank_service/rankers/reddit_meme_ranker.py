# src/rankers/reddit_meme_ranker.py
import math
from datetime import datetime, timezone
from src.models import RedditPost
from src.utils.common import clamp
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class RedditMemeRanker:
    """Ранкер для игровых мемов с использованием констант."""

    def _engagement_score(self, post: RedditPost) -> float:
        """
        Рассчитывает базовую вовлечённость по апвоутам и комментам.
        Использует логарифмическое сглаживание и мягкий cap.
        """
        ups = float(min(post.ups or post.score or 0, C.REDDIT_MEME_RANKER_MAX_UPS))
        comments = float(min(post.num_comments or 0, C.REDDIT_MEME_RANKER_MAX_COMMENTS))

        engagement = (
            math.log1p(ups) * C.REDDIT_MEME_RANKER_UPS_WEIGHT +
            math.log1p(comments) * C.REDDIT_MEME_RANKER_COMMENTS_WEIGHT
        )

        return clamp(engagement / C.REDDIT_MEME_RANKER_ENGAGEMENT_NORM, 0.0, 1.0)

    def _freshness_decay(self, post: RedditPost) -> float:
        """
        Возвращает коэффициент затухания по времени.
        Для мемов слабее, чем для новостей — старые мемы всё ещё ценны.
        """
        if not post.created_utc:
            return 1.0

        now_ts = datetime.now(timezone.utc).timestamp()
        age_days = (now_ts - post.created_utc.timestamp()) / C.SECONDS_IN_DAY

        decay = 1 / (1 + (age_days / C.REDDIT_MEME_RANKER_HALFLIFE_DAYS))
        return clamp(decay, C.REDDIT_MEME_RANKER_MIN_DECAY, 1.0)

    def evaluate(self, post: RedditPost) -> float:
        """
        Возвращает финальный рейтинг мема (0..1)
        """
        engagement = self._engagement_score(post)
        freshness = self._freshness_decay(post)

        final_score = engagement * freshness
        return clamp(final_score, 0.0, 1.0)
