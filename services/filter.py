from __future__ import annotations
from models.game import GameModel
from models.igdb import IGDBMeta
from config.settings import settings
from config import constants as C
from datetime import datetime


class GameFilter:
    """
    Publication filter that combines score threshold with domain rules using
    both Steam (`GameModel`) and IGDB (`IGDBMeta`) data.
    """

    def __init__(self, threshold: float | None = None) -> None:
        self._threshold = threshold if threshold is not None else settings.SCORE_PUBLISH_THRESHOLD

    def should_publish(self, game: GameModel, meta: IGDBMeta | None, score: float) -> bool:
        # 1) Score threshold
        if score < self._threshold:
            return False

        # 2) Name blacklists (DLC, soundtrack, demo, etc.)
        if not self._pass_name_blacklist(game):
            return False

        # 3) Genre/content blacklists (education/tutorial, etc.)
        if not self._pass_genre_blacklist(game, meta):
            return False

        # 4) Asset sanity checks (header image by default)
        if C.FILTER_REQUIRE_HEADER_IMAGE and not game.header_image:
            return False

        # 5) Price sanity (too expensive for target audience unless free)
        if not self._pass_price_cap(game, score):
            return False

        # 6) Recency (older titles usually skipped unless strong score)
        if not self._pass_recency(game, meta, score):
            return False

        # 7) IGDB quality/popularity basic floors if meta is present
        if meta and not self._pass_igdb_quality(meta, score):
            return False

        return True

    def _pass_name_blacklist(self, game: GameModel) -> bool:
        name_low = (game.name or "").lower()
        return not any(tok in name_low for tok in C.FILTER_NAME_BLACKLIST_TOKENS)

    def _pass_genre_blacklist(self, game: GameModel, meta: IGDBMeta | None) -> bool:
        g = set((game.genres or []))
        if meta:
            g.update(meta.genres or [])
        g_low = {x.lower() for x in g}
        bl = {x.lower() for x in C.FILTER_GENRE_BLACKLIST}
        return len(g_low.intersection(bl)) == 0

    def _pass_price_cap(self, game: GameModel, score: float) -> bool:
        if game.is_free:
            return True
        if not game.price:
            # unknown price: allow but rely on score and other signals
            return True
        price = game.price.final
        # allow higher price if score is very high
        cap = (
            C.FILTER_MAX_PRICE
            if score >= (self._threshold + C.PRICE_CAP_RELAX_SCORE_DELTA)
            else (C.FILTER_MAX_PRICE * C.PRICE_CAP_STRICT_FACTOR)
        )
        return price <= cap

    def _pass_recency(self, game: GameModel, meta: IGDBMeta | None, score: float) -> bool:
        dt = meta.release_date if (meta and meta.release_date) else game.release_date
        if not dt:
            # unknown release date: allow, other checks will gate
            return True
        years = (datetime.utcnow() - dt).days / C.RECENCY_YEAR_DENOMINATOR
        if years <= C.FILTER_MAX_YEARS_SINCE_RELEASE:
            return True
        # If older than max, only allow with strong score
        return score >= C.FILTER_MIN_SCORE_FOR_OLD_TITLES

    def _pass_igdb_quality(self, meta: IGDBMeta, score: float) -> bool:
        m = meta.metrics
        if not m:
            return True
        # Popularity floor
        pop_sum = (m.follows or 0) + (m.hypes or 0)
        if pop_sum < C.FILTER_MIN_POPULARITY_SUM and score < (self._threshold + C.IGDB_FLOOR_RELAX_DELTA):
            return False
        # Rating count floor; tolerate if score strong
        if (m.rating_count or 0) < C.FILTER_MIN_IGDB_RATING_COUNT and score < (self._threshold + C.IGDB_FLOOR_RELAX_DELTA):
            return False
        return True
