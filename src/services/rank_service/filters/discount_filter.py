from datetime import datetime
from typing import Optional
from src.models.game import GameSnapshot
from src.schemas.publication_schemas import DiscountPublicationSchema
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class DiscountFilter:

    def detect_discount(self, game, snapshots: list[GameSnapshot]) -> Optional[DiscountPublicationSchema]:
        if not snapshots or len(snapshots) < 2:
            return None

        # Сортируем снапшоты по дате
        snapshots = sorted(snapshots, key=lambda s: s.created_at)
        with_min_price, with_max_price = min(snapshots, key=lambda s: s.price), max(snapshots, key=lambda s: s.price)

        if not with_min_price.price or not with_max_price.price or with_min_price.price <= 0:
            return None

        # Расчёт падения цены
        percent_drop = 100 * (with_min_price.price - with_max_price.price) / with_min_price.price
        absolute_drop = with_min_price.price - with_max_price.price

        if percent_drop <= 0:
            return None  # цена выросла или не изменилась

        # Динамический порог в зависимости от цены
        dynamic_threshold = self._dynamic_threshold(with_min_price.price)

        if percent_drop >= dynamic_threshold:
            return DiscountPublicationSchema(
                game_id=game.id,
                old_price=with_min_price.price,
                new_price=with_max_price.price,
                percent_drop=round(percent_drop, 2),
                absolute_drop=round(absolute_drop, 2),
                detected_at=datetime.now(),
            )
        return None

    def _dynamic_threshold(self, price: float) -> float:
        """Регулирует порог скидки в зависимости от стоимости игры."""
        if price < C.LOW_PRICE_THRESHOLD:
            return C.LOW_PRICE_DROP_PERCENT
        elif price < C.MID_PRICE_THRESHOLD:
            return C.MID_PRICE_DROP_PERCENT
        elif price < C.HIGH_PRICE_THRESHOLD:
            return C.HIGH_PRICE_DROP_PERCENT
        else:
            return C.PREMIUM_PRICE_DROP_PERCENT