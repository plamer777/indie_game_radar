from __future__ import annotations
from typing import Optional, Iterable
from src.models.game import GameModel, ReviewResponse, NewsStats, GameSnapshot
from src.models import IGDBMeta, PopularityMetrics
from src.config import constants as C
from math import log1p
from datetime import datetime
from src.schemas import GameSnapshotSchema
from src.utils.common import clamp, safe_div
# ---------------------------------------------------------------------------------------------------------------------


class GameRanker:

    async def evaluate(
        self,
        game: GameModel,
        meta: Optional[IGDBMeta],
        snapshots: list[GameSnapshot | GameSnapshotSchema],
    ) -> float:
        """
        Compute final game score in [0, 1] using both IGDB and Steam metrics.
        Handles cases where meta data is missing and applies volatility/completeness adjustments.
        """

        ext = game.ext_info or None
        metrics = meta.metrics if meta else None

        # ---- 1. Trend & Volatility ----
        trend_metrics = self._compute_trend(snapshots)
        volatility = self._compute_volatility(snapshots)
        avg_players = self._compute_avg_players(snapshots)
        # completeness_factor = min(1.0, len(snapshots) / C.MIN_SNAPSHOTS_REQUIRED)

        # ---- 2. IGDB ----
        rating = self._rating_component(metrics)
        popularity = self._popularity_component(metrics)
        recency = self._recency_component(game, meta)

        # ---- 3. Steam ----
        price_attr = self._price_attr_component(game)
        discount = self._discount_component(game)
        review = self._review_component(ext.review_summary if ext else None)
        news = self._news_component(ext.news_stats if ext else None)

        # ---- 4. Recommendations ----
        recommendations = 0.0
        if getattr(game, "recommendations", None):
            rec_count = game.recommendations or 0
            # лог-нормализация
            recommendations = min(1.0, log1p(rec_count) / C.RECOMMENDATION_LOG_SCALE)

        # ---- 5. Recency boost ----
        recency_boost = 1.0
        if game.release_date:
            age_days = (datetime.now() - game.release_date).days
            if age_days < C.RECENT_GAME_AGE_DAYS:
                # плавное затухание усиления со временем
                recency_boost = C.RECENCY_BASE_BOOST - (age_days / C.RECENCY_FADE_DIVISOR)
                recency_boost = clamp(recency_boost, 1.0, C.RECENCY_MAX_BOOST)

        # ---- 6. Trend ----
        trend_value = clamp(trend_metrics.get("momentum", 0.0), 0.0, 1.0)

        # ---- 7. Adaptive IGDB factor ----
        igdb_factor = C.IGDB_FULL_DATA_FACTOR if (meta and metrics) else C.IGDB_PARTIAL_DATA_FACTOR

        # ---- 8. Aggregation ----
        review_strength = (review * C.REVIEW_WEIGHT + recommendations * C.RECOMMENDATION_WEIGHT) * recency_boost

        raw_score = (
            igdb_factor * (
            C.WEIGHT_RATING * rating +
            C.WEIGHT_POPULARITY * popularity +
            C.WEIGHT_RECENCY * recency
        )
            + C.WEIGHT_USER_SENTIMENT * review_strength
            + C.WEIGHT_NEWS * news
            + C.WEIGHT_PRICE_ATTRACTIVENESS * price_attr
            + C.WEIGHT_DISCOUNT * discount
            + C.WEIGHT_TREND * trend_value
            + C.WEIGHT_ACTIVITY * avg_players
        )

        final_score = (raw_score - volatility)
        final_score = clamp(final_score, 0.0, 1.0)

        return float(final_score)

    def _compute_avg_players(self, snapshots: list[GameSnapshotSchema]):
        avg_players = 0.0
        if snapshots:
            vals = [s.current_players for s in snapshots if s.current_players is not None]
            if vals:
                avg_players = sum(vals) / len(vals)
                # логарифмическое сглаживание: 0..1 при 0..~50к игроков
                avg_players = clamp(log1p(avg_players) / log1p(50000), 0.0, 1.0)

        return avg_players

    def _get_recent_snapshots(
        self, snapshots: Iterable[GameSnapshotSchema], n: int
    ) -> list[GameSnapshotSchema]:
        snaps = sorted((s for s in snapshots if s is not None), key=lambda s: s.snapshot_time)
        if not snaps:
            return []
        return snaps[-n:]

    def _compute_trend(self, snaps: list[GameSnapshotSchema]) -> dict[str, float]:
        """
        Compute growth, avg_growth, momentum from list of recent snapshots.
        Returns dict with:
          - growth: relative growth between first and last: (last - first) / max(first,1)
          - avg_growth: average of per-step relative changes
          - momentum: smoothed value in [ -1.0 .. +1.0 ] (positive = upward momentum)
        """
        if not snaps or len(snaps) < 2:
            return {"growth": 0.0, "avg_growth": 0.0, "momentum": 0.0}

        # extract current_players and review_ratio series (use 0 defaults)
        players = [s.current_players or 0 for s in snaps]
        reviews = [s.review_ratio or 0.0 for s in snaps]

        # use players primarily; if players all zeros, fallback to review_ratio growth
        use_players = any(p > 0 for p in players)

        if use_players:
            series = players
        else:
            series = [int(r * 1000) for r in reviews]  # scale reviews to comparable ints

        # growth: relative from first to last
        first = series[0]
        last = series[-1]
        growth = safe_div((last - first), max(first, 1), 0.0)

        # per-step relative changes
        rel_changes = []
        for i in range(1, len(series)):
            prev = series[i - 1]
            cur = series[i]
            rel = safe_div((cur - prev), max(prev, 1), 0.0)
            rel_changes.append(rel)

        avg_growth = safe_div(sum(rel_changes), len(rel_changes), 0.0) if rel_changes else 0.0

        # momentum: combine growth and avg_growth, apply gentle nonlinear scaling
        # we map combined to -1..1 via tanh-like scaling using log1p for smoothing
        combined = growth * 0.6 + avg_growth * 0.4  # weighted mixture
        # clamp combined to reasonable range first
        combined_clamped = max(-2.0, min(2.0, combined))  # avoid overflow
        # use a simple smooth transform to -1..1:
        # momentum = combined_clamped / (1 + abs(combined_clamped))  -> maps to (-1,1)
        momentum = safe_div(combined_clamped, (1.0 + abs(combined_clamped)), 0.0)

        # finally normalize to 0..1 if you prefer positive-only contribution later
        # keep momentum as is (-1..1) for diagnostics; evaluate() uses positive part only
        return {"growth": float(growth), "avg_growth": float(avg_growth), "momentum": float(momentum)}

    def _compute_volatility(self, snaps: list[GameSnapshotSchema]) -> float:
        """
        Compute volatility penalty based on players variations across snapshots.
        Returns penalty in [0.0, max_penalty], where default max_penalty ~ 0.1 (configurable).
        """
        if not snaps or len(snaps) < 3:
            return 0.0

        vals = [s.current_players for s in snaps if s.current_players is not None]
        if len(vals) < 3:
            # fallback to review_ratio volatility
            vals = [int((s.review_ratio or 0.0) * 1000) for s in snaps if s.review_ratio is not None]
            if len(vals) < 3:
                return 0.0

        # compute mean and std-like avg absolute diff
        diffs = [abs(vals[i] - vals[i - 1]) for i in range(1, len(vals))]
        mean_diff = sum(diffs) / len(diffs)
        mean_val = sum(vals) / len(vals) if vals else 0.0

        rel_vol = safe_div(mean_diff, max(mean_val, 1.0), 0.0)  # relative volatility

        # map to penalty. scale factor to keep penalty small.
        # choose max_penalty from constants or default 0.12
        penalty = clamp(rel_vol * C.VOLATILITY_SENSITIVITY, 0.0, C.VOLATILITY_MAX_PENALTY)
        return float(penalty)

    def _rating_component(self, metrics: Optional[PopularityMetrics]) -> float:
        if not metrics or metrics.rating is None:
            return 0.0
        # normalize 0..100 to 0..1; add softness by count
        base = (metrics.rating or 0) / 100.0
        count_factor = log1p(metrics.rating_count or 0) / log1p(C.RATING_COUNT_LOG_NORMALIZER)
        return base * min(1.0, C.RATING_COUNT_BLEND_BASE + C.RATING_COUNT_BLEND_SCALE * count_factor)

    def _news_component(self, news: Optional[NewsStats]) -> float:
        if not news:
            return 0.0

        # Чем меньше прошло времени с последней новости, тем лучше
        recency_factor = 1.0 - min(1.0, (news.days_since_last_news or 999) / C.NEWS_DECAY_DAYS)

        # Активность за последние 90 дней (до 5 новостей = максимум)
        activity_factor = min(1.0, news.total_news_last_90d / C.NEWS_ACTIVITY_NORMALIZER)

        # Усреднение с приоритетом свежести
        return round(0.7 * recency_factor + 0.3 * activity_factor, 3)

    def _review_component(self, review: Optional[ReviewResponse]) -> float:
        if not review or not review.ratio or not review.total_reviews:
            return 0.0

        # ratio в диапазоне [0, 1], весим его количеством отзывов
        volume_factor = min(1.0, log1p(review.total_reviews) / log1p(C.REVIEW_VOLUME_NORMALIZER))
        return review.ratio * volume_factor

    def _popularity_component(self, metrics: Optional[PopularityMetrics]) -> float:
        if not metrics:
            return 0.0
        f = log1p(metrics.follows or 0)
        h = log1p(metrics.hypes or 0)
        total = f + C.POPULARITY_HYPE_WEIGHT * h
        return min(1.0, total / log1p(C.POPULARITY_LOG_NORMALIZER))

    def _recency_component(self, game: GameModel, meta: Optional[IGDBMeta]) -> float:
        dt = meta.release_date if (meta and meta.release_date) else game.release_date
        if not dt:
            return C.UNKNOWN_RECENCY_BASE  # unknown recency, small bias
        dt = dt.replace(tzinfo=None)
        days = (datetime.now() - dt).days
        if days <= 0:
            return 1.0
        return max(0.0, 1.0 - min(1.0, days / C.RECENCY_YEAR_DENOMINATOR))

    def _price_attr_component(self, game: GameModel) -> float:
        if game.is_free:
            return 1.0
        if not game.price:
            return 0.5
        price = game.price.final
        # Prefer < $15
        # bucketed pricing attractiveness
        limits = C.PRICE_BUCKETS_USD
        scores = C.PRICE_BUCKET_SCORES
        for limit, s in zip(limits, scores):
            if price <= limit:
                return s
        return scores[-1]

    def _discount_component(self, game: GameModel) -> float:
        if not game.price:
            return 0.0
        return min(1.0, (game.price.discount_percent or 0) / C.DISCOUNT_NORMALIZE_MAX)
