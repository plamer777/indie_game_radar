from __future__ import annotations
from src.models.game import GameModel
from src.models import IGDBMeta
from src.config import constants as C
from datetime import datetime
# ---------------------------------------------------------------------------------------------------------------------


class GameFilter:
    """
    Publication filter that combines score threshold with domain rules using
    both Steam (`GameModel`) and IGDB (`IGDBMeta`) data.
    """

    def __init__(self, threshold: float | None = C.SCORE_PUBLISH_THRESHOLD) -> None:
        self._threshold = threshold

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
        if not self._pass_recency(game, meta):
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

    def _pass_recency(self, game: GameModel, meta: IGDBMeta | None) -> bool:
        dt = meta.release_date if (meta and meta.release_date) else game.release_date
        if not dt:
            # unknown release date: allow, other checks will gate
            return True
        days_from_release = (datetime.now() - dt).days
        if days_from_release <= C.GAME_RANKER_RECENCY_DELTA_DAYS:
            return True

        return False
