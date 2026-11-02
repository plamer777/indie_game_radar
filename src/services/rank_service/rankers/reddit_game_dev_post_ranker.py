import math
from datetime import datetime
from typing import Optional
from src.models import RedditPost
from src.utils.common import clamp, clean_html
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class RedditDevPostRanker:
    """
    Ranks gamedev posts: personal stories, tips, behind-the-scenes,
    lessons learned, postmortems, etc.
    """

    def _length_penalty(self, text: str) -> float:
        if not text:
            return 0.0

        if len(text) < C.REDDIT_GAME_DEV_STORY_MIN_CONTENT_LENGTH:
            return len(text) / C.REDDIT_GAME_DEV_STORY_MIN_CONTENT_LENGTH
        return 1.0

    def _is_technical_post(self, text: str) -> bool:
        if not text:
            return False
        lower = text.lower()
        # if >2 tech words — likely a changelog
        matches = sum(kw in lower for kw in C.REDDIT_TECH_KEYWORDS)
        return matches >= 2

    def _is_story_post(self, text: str) -> bool:
        """Detects whether the post is narrative/experience-based."""
        if not text:
            return False
        lower = text.lower()

        return any(p in lower for p in C.REDDIT_GAME_DEV_STORY_PATTERNS)

    def _contains_promo_signals(self, text: str, flair: Optional[str]) -> bool:
        lower = (text or "").lower() + " " + (flair or "").lower()
        for kw in ["sale", "discount", "wishlist", "available now", "release"]:
            if kw in lower:
                return True
        return False

    def _engagement_score(self, post: RedditPost) -> float:
        ups = float(post.ups or post.score or 0)
        comments = float(post.num_comments or 0)
        awards = float(post.total_awards_received or 0)
        ratio = float(post.upvote_ratio or 1.0)
        media = 1.0 if post.preview_images or post.is_video else 0.0

        raw = (
            ups * ratio +
            comments * C.REDDIT_GAME_DEV_STORY_COMMENT_WEIGHT +
            awards * C.REDDIT_AWARD_WEIGHT +
            media * C.REDDIT_MEDIA_WEIGHT
        )
        eng = math.log1p(raw) / (1.0 + math.log1p(raw))
        return clamp(eng, 0.0, 1.0)

    def _subreddit_quality(self, post: RedditPost) -> float:
        subs = (post.subreddit or "").lower()
        if subs in C.REDDIT_HIGH_QUALITY_SUBREDDITS:
            base = 1.0
        else:
            base = 0.6

        if post.subreddit_subscribers:
            boost = min(1.0, math.log1p(post.subreddit_subscribers) / 10.0)
            base *= (0.8 + 0.4 * boost)

        return clamp(base, 0.3, 1.3)

    def _storytelling_value(self, cleaned_text: str) -> float:
        """Scores the value of storytelling and insight."""
        if not cleaned_text:
            return 0.0
        lower = cleaned_text.lower()
        score = 0.5
        if self._is_story_post(lower):
            score += 0.3
        if "lesson" in lower or "learned" in lower:
            score += 0.1
        if "postmortem" in lower or "journey" in lower:
            score += 0.1
        if "mistake" in lower or "failure" in lower:
            score += 0.1
        return clamp(score, 0.0, 1.0)

    # ------------------- main method -------------------

    def evaluate(self, post: RedditPost) -> float:
        now = datetime.now()
        age_days = (now - post.created_utc).days if post.created_utc else 9999
        freshness = clamp(1.0 - age_days / C.REDDIT_MAX_POST_AGE_DAYS, 0.0, 1.0)  # freshness

        source_weight = self._subreddit_quality(post)
        engagement = self._engagement_score(post)

        cleaned = clean_html(post.selftext_html or post.selftext or "")
        length_factor = self._length_penalty(cleaned)
        storytelling = self._storytelling_value(cleaned)

        is_tech = self._is_technical_post(cleaned)
        is_promo = self._contains_promo_signals(cleaned, post.link_flair_text)

        # combined score
        base = (
            C.REDDIT_DEV_WEIGHT_FRESHNESS * freshness +
            C.REDDIT_DEV_WEIGHT_SOURCE * source_weight +
            C.REDDIT_DEV_WEIGHT_ENGAGEMENT * engagement +
            C.REDDIT_DEV_WEIGHT_STORYTELLING * storytelling
        )

        if is_tech:
            base *= C.REDDIT_DEV_TECH_PENALTY
        if is_promo:
            base *= C.REDDIT_DEV_PROMO_PENALTY

        base *= (C.REDDIT_DEV_LENGTH_BASE + C.REDDIT_DEV_LENGTH_SCALE * length_factor)

        return clamp(base, 0.0, 1.0)
