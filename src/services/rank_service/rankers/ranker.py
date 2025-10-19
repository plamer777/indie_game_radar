from __future__ import annotations
from typing import Optional
from src.models.game import GameModel, ReviewResponse, NewsStats
from src.models import IGDBMeta, PopularityMetrics
from src.config import constants as C
from math import log1p
from datetime import datetime, UTC

from src.schemas import GameSnapshotSchema


# ---------------------------------------------------------------------------------------------------------------------


class GameRanker:
    def __init__(self) -> None:
        pass

    async def evaluate(
            self, game: GameModel, meta: Optional[IGDBMeta], snapshots: list[GameSnapshotSchema]
    ) -> float:
        metrics = meta.metrics if meta else None
        ext = game.ext_info or None
        delta, delta_history = self._compute_snapshot_deltas(snapshots)

        rating = self._rating_component(metrics)
        popularity = self._popularity_component(metrics)
        recency = self._recency_component(game, meta)
        price_attr = self._price_attr_component(game)
        discount = self._discount_component(game)
        trend = self._trend_component(delta)
        penalty = self._volatility_penalty(delta_history)
        review = self._review_component(ext.review_summary if ext else None)
        news = self._news_component(ext.news_stats if ext else None)

        score = (
                C.WEIGHT_RATING * rating
                + C.WEIGHT_POPULARITY * popularity
                + C.WEIGHT_RECENCY * recency
                + C.WEIGHT_REVIEW * review
                + C.WEIGHT_NEWS * news
                + C.WEIGHT_PRICE_ATTRACTIVENESS * price_attr
                + C.WEIGHT_DISCOUNT * discount
                + C.WEIGHT_TREND * trend
                - penalty
        )

        return max(0.0, min(1.0, score))

    def _compute_snapshot_deltas(
        self, snapshots: list[GameSnapshotSchema]
    ) -> tuple[Optional[dict], list[dict]]:
        """
        Возвращает:
          delta — изменения между последними двумя снапшотами
          delta_history — история относительных изменений
        """
        if not snapshots or len(snapshots) < 2:
            return None, []

        # сортируем по времени
        snapshots = sorted(snapshots, key=lambda s: s.snapshot_time)

        delta_history = []
        for prev, cur in zip(snapshots[:-1], snapshots[1:]):
            d_players = (cur.current_players or 0) - (prev.current_players or 0)
            rel_players = (
                (d_players / prev.current_players) if prev.current_players else 0.0
            )
            d_review = (cur.review_ratio or 0) - (prev.review_ratio or 0)
            delta_history.append(
                {
                    "players_change": d_players,
                    "players_change_rel": rel_players,
                    "review_ratio_change": d_review,
                }
            )

        # Последний элемент — актуальный delta
        delta = delta_history[-1] if delta_history else None
        return delta, delta_history

    # -----------------------------------------------------------------------------------------------------------------
    def _trend_component(self, delta: Optional[dict]) -> float:
        if not delta:
            return 0.0
        score = 0.0

        rel = delta.get("players_change_rel")
        if rel and rel > 0:
            score += min(rel, 0.2)

        rr = delta.get("review_ratio_change")
        if rr and rr > 0:
            score += min(rr * 2, 0.2)

        return min(score, 1.0)

    def _volatility_penalty(self, delta_history: Optional[list[dict]]) -> float:
        if not delta_history or len(delta_history) < 2:
            return 0.0
        diffs = [abs(d.get("players_change", 0)) for d in delta_history]
        avg = sum(diffs) / len(diffs)
        if avg > C.PLAYER_CHANGE_VOLATILITY_THRESHOLD:
            return (avg / (avg + C.PLAYER_CHANGE_VOLATILITY_THRESHOLD)) * 0.1
        return 0.0

    def _compute_steam_review_ratio(self, review_summary: ReviewResponse) -> float:
        if not review_summary or not review_summary.reviews:
            return 0.0
        total = len(review_summary.reviews)
        up = sum(1 for r in review_summary.reviews if r.voted_up)
        return up / total

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
        days = (datetime.now(UTC) - dt).days
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
