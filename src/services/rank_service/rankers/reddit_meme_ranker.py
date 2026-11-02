# src/rankers/reddit_meme_ranker.py
import math
from datetime import datetime, timezone
from src.models import RedditPost
from src.utils.common import clamp
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class RedditMemeRanker:
    """Ranker for gaming memes driven by constants."""

    def _engagement_score(self, post: RedditPost) -> float:
        """
        Computes base engagement from upvotes and comments.
        Uses logarithmic smoothing and a soft cap.
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
        Returns the time-decay coefficient.
        Weaker for memes than for news — old memes are still valuable.
        """
        if not post.created_utc:
            return 1.0

        now_ts = datetime.now(timezone.utc).timestamp()
        age_days = (now_ts - post.created_utc.timestamp()) / C.SECONDS_IN_DAY

        decay = 1 / (1 + (age_days / C.REDDIT_MEME_RANKER_HALFLIFE_DAYS))
        return clamp(decay, C.REDDIT_MEME_RANKER_MIN_DECAY, 1.0)

    def evaluate(self, post: RedditPost) -> float:
        """
        Returns the final meme score (0..1)
        """
        engagement = self._engagement_score(post)
        freshness = self._freshness_decay(post)

        final_score = engagement * freshness
        return clamp(final_score, 0.0, 1.0)
