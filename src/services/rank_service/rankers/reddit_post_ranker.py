# src/rankers/reddit_post_ranker.py
import math
import re
from datetime import datetime
from typing import Optional
from src.models import RankedGameModel  # как у тебя
from src.models import RedditPost
from src.utils.common import clamp, clean_html
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class RedditPostRanker:
    def __init__(self, game_rank_lookup=None) -> None:
        """
        :param game_rank_lookup: callable(game_id) -> last_score (0..1)
        :param high_quality_subreddits: optional set of subreddit names that should be treated as high-quality/dev
        """
        self.game_rank_lookup = game_rank_lookup or (lambda gid: 0.0)

    def _length_penalty(self, text: str) -> float:
        min_len = C.MIN_NEWS_CONTENT_LENGTH
        if len(text) < min_len:
            return len(text) / min_len
        return 1.0

    def _is_technical_changelog(self, raw: str, cleaned: str) -> bool:
        if not cleaned and not raw:
            return False
        lower_raw = (raw or "").lower()
        lower_text = (cleaned or "").lower()
        list_token_count = lower_raw.count("<li>") + lower_raw.count("[*]") + lower_raw.count("- ") + lower_raw.count("* ")
        bullet_lines = re.findall(r"(?m)^[\s]*[-\*\u2022]\s+", raw or "")
        list_token_count += len(bullet_lines)

        lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
        list_like_lines = sum(1 for ln in lines if re.match(r"^(-|\*|•|\d+\.)\s+", ln) or len(ln.split()) < 10)
        total_words = len(cleaned.split())
        list_density = 0.0
        if total_words > 0:
            list_density = (list_token_count * 5 + list_like_lines) / (total_words / 10 + 1)

        has_tech_kw = any(kw in lower_text for kw in C.REDDIT_TECH_KEYWORDS)
        fraction_list_lines = (list_like_lines / len(lines)) if lines else 0.0

        is_tech = (
            list_token_count >= C.REDDIT_TECH_LIST_TOKEN_THRESHOLD
            or fraction_list_lines >= C.REDDIT_TECH_LIST_LINE_RATIO
            or list_density >= C.REDDIT_TECH_LIST_DENSITY_THRESHOLD
        ) and has_tech_kw

        return bool(is_tech)

    def _contains_dev_keywords(self, text: str) -> bool:
        if not text:
            return False
        lower = text.lower()
        for kw in C.REDDIT_DEVLOG_KEYWORDS:
            if kw in lower:
                return True
        return False

    def _contains_low_value_keywords(self, text: str) -> bool:
        if not text:
            return False
        lower = text.lower()
        for kw in C.REDDIT_LOW_VALUE_KEYWORDS:
            if kw in lower:
                return True
        return False

    def _engagement_score(self, post: RedditPost) -> float:
        """
        Рассчитывает нормализованный engagement score (0..1)
        на основе активности и реакции пользователей.
        """
        ups = float(post.ups or post.score or 0)
        downs = float(post.downs or 0)
        comments = float(post.num_comments or 0)
        awards = float(post.total_awards_received or 0)
        crossposts = float(post.num_crossposts or 0)
        ratio = float(post.upvote_ratio or 1.0)
        media = 1.0 if post.preview_images or post.is_video else 0.0

        # Базовая метрика вовлечённости с учётом спорности
        # Высокие upvotes при низком ratio → контент спорный, понижаем вес
        # Высокий ratio усиливает позитивную вовлечённость
        positive = ups * ratio
        negative = downs * (1.0 - ratio)
        raw = (
            positive * 1.0
            - negative * 0.5
            + comments * 1.5
            + awards * 10.0
            + crossposts * 2.0
            + media * 15.0
        )

        # логарифмическое сглаживание для ограничения экстремальных значений
        eng = math.log1p(raw) / (1.0 + math.log1p(raw))

        return clamp(eng, 0.0, 1.0)

    def _subreddit_quality(self, post: RedditPost) -> float:
        # base weight by membership and known HQ subreddits
        subs = post.subreddit.lower() if post.subreddit else ""
        if subs in C.REDDIT_HIGH_QUALITY_SUBREDDITS:
            base = C.REDDIT_SUBREDDIT_HIGH_WEIGHT
        else:
            base = C.REDDIT_SUBREDDIT_DEFAULT_WEIGHT

        # boost slightly with subscribers if available (log scale)
        if post.subreddit_subscribers:
            import math
            boost = min(1.0, math.log1p(post.subreddit_subscribers) / 10.0)  # tuned heuristic
            base = base * (0.8 + 0.4 * boost)  # keep within reasonable bounds
        return clamp(base, 0.0, 1.5)

    def _info_value_score(self, cleaned_text: str, post: RedditPost) -> float:
        if not cleaned_text:
            return 0.0
        lower = cleaned_text.lower()
        score = 0.45  # baseline

        # high/medium/low keywords from C (reuse same lists)
        for kw in C.REDDIT_HIGH_VALUE_KEYWORDS:
            if kw in lower:
                score += 0.3
        for kw in C.REDDIT_MEDIUM_VALUE_KEYWORDS:
            if kw in lower:
                score += 0.08
        for kw in C.REDDIT_LOW_VALUE_KEYWORDS:
            if kw in lower:
                score -= 0.25

        # reward if post has preview images or video (likely richer)
        if post.preview_images or post.is_video:
            score += C.REDDIT_MEDIA_INFO_BONUS

        # reward if domain is steam, itch, github (developer resources)
        domain = (post.domain or "").lower()
        if any(d in domain for d in C.REDDIT_HIGH_VALUE_DOMAINS):
            score += 0.12

        # small penalty if clearly promotional flair (like Promotion / Giveaway)
        flair = (post.link_flair_text or "").lower() if post.link_flair_text else ""
        if any(p in flair for p in C.REDDIT_LOW_VALUE_KEYWORDS):
            score -= 0.3

        return clamp(score, 0.0, 1.0)

    # ------------------ main evaluate ------------------
    def evaluate(self, game: RankedGameModel, post: RedditPost) -> float:
        now = datetime.now()

        # 1) Freshness
        age_days = (now - post.created_utc).days if post.created_utc else 9999
        freshness = clamp(1.0 - age_days / C.REDDIT_MAX_POST_AGE_DAYS, 0.0, 1.0)

        # 2) Subreddit / source quality
        source_weight = self._subreddit_quality(post)

        # 3) Engagement
        engagement = self._engagement_score(post)

        # 4) Content richness & info value
        raw_html = post.selftext_html or post.selftext or ""
        cleaned = clean_html(raw_html)
        length_factor = self._length_penalty(cleaned)
        info_value = self._info_value_score(cleaned, post)
        content_richness = clamp(len(cleaned) / C.REDDIT_MAX_CONTENT_LENGTH, 0.0, 1.0)
        # media bonus
        if post.preview_images or post.is_video:
            content_richness = min(1.0, content_richness + C.REDDIT_MEDIA_BONUS)

        content_score = content_richness * info_value * length_factor

        # 5) Detect technical/changelog or low-value promo and adjust
        is_technical = self._is_technical_changelog(raw_html, cleaned)
        is_low_value = (
            self._contains_low_value_keywords(cleaned) or
            (
                post.link_flair_text and
                any(kw.lower() in (post.link_flair_text or "").lower() for kw in C.LOW_VALUE_KEYWORDS)
            )
        )
        if is_technical:
            content_score *= C.REDDIT_TECHNICAL_POST_MULTIPLIER
        if is_low_value:
            content_score *= C.REDDIT_LOW_VALUE_MULTIPLIER

        # 6) Developer signal boost
        dev_signal = 0.0
        # flair or link_flair indicates dev
        if (
            post.link_flair_text and
            any(kw.lower() in (post.link_flair_text or "").lower() for kw in C.REDDIT_DEV_FLAIR_KEYWORDS)
        ):
            dev_signal += 0.3
        # subreddit known as dev
        if (post.subreddit or "").lower() in C.REDDIT_HIGH_QUALITY_SUBREDDITS:
            dev_signal += 0.2
        # text contains dev keywords
        if self._contains_dev_keywords(cleaned):
            dev_signal += 0.15
        dev_signal = clamp(dev_signal, 0.0, 1.0)

        # 7) Game quality influence
        game_quality = clamp(game.last_score or self.game_rank_lookup(game.id), 0.0, 1.0)
        if info_value < C.REDDIT_INFO_VALUE_GAME_QUALITY_THRESHOLD:
            game_quality *= C.REDDIT_GAME_QUALITY_REDUCTION_FACTOR
        if is_technical:
            game_quality *= C.REDDIT_GAME_QUALITY_TECH_MULTIPLIER

        # 8) combine raw score (weights configurable via C)
        raw_score = (
            C.REDDIT_WEIGHT_FRESHNESS * freshness +
            C.REDDIT_WEIGHT_SOURCE * source_weight +
            C.REDDIT_WEIGHT_ENGAGEMENT * engagement +
            C.REDDIT_WEIGHT_CONTENT_RICHNESS * content_score +
            C.REDDIT_WEIGHT_DEV_SIGNAL * dev_signal +
            C.REDDIT_WEIGHT_GAME_QUALITY * game_quality
        )

        # 9) recency boost based on game release (same logic as NewsRanker)
        recency_boost = 1.0
        if game.release_date:
            game_age_days = (now - game.release_date).days
            decay_days = C.REDDIT_RECENCY_BOOST_DECAY_DAYS
            if game_age_days < decay_days:
                rb_max = C.REDDIT_RECENCY_BOOST_MAX
                recency_boost = 1.0 + (rb_max - 1.0) * (1 - game_age_days / decay_days)
                recency_boost = clamp(recency_boost, 1.0, rb_max)

        final = clamp(raw_score * recency_boost, 0.0, 1.0)

        return float(final)
