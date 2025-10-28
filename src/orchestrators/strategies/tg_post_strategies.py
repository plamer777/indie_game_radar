import random
from datetime import datetime
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class ContentAllocationStrategy:
    """
    Распределяет публикации по источникам с учетом времени и доступных данных.
    """
    def __init__(self, news: list[dict], games: list[dict], discounts: list[dict]):
        self.news = news
        self.games = games
        self.discounts = discounts

    def _get_time_segment(self) -> str:
        """Определяем текущее время суток для распределения."""
        hour = datetime.now().hour
        for segment, (start, end) in C.TIME_WINDOWS.items():
            if start <= hour < end:
                return segment
        # по умолчанию считаем утро (например, если ночью)
        return "morning"

    def _allocate_slots(self, total_posts: int, priorities: dict[str, float]) -> dict[str, int]:
        """Рассчитываем, сколько постов выделить под каждую категорию."""
        base_allocation = {k: int(total_posts * v) for k, v in priorities.items()}

        # Корректируем, если из-за округлений не набралось ровно total_posts
        allocated = sum(base_allocation.values())
        if allocated < total_posts:
            diff = total_posts - allocated
            # добавляем недостающие слоты по убыванию приоритета
            sorted_keys = sorted(priorities.keys(), key=lambda k: priorities[k], reverse=True)
            for k in sorted_keys[:diff]:
                base_allocation[k] += 1
        return base_allocation

    def _redistribute_if_needed(self, allocation: dict[str, int]) -> dict[str, int]:
        """Если контента не хватает, перераспределяем в пользу других категорий."""
        available = {
            "news": len(self.news),
            "games": len(self.games),
            "discounts": len(self.discounts),
        }

        deficit = {}

        # Вычисляем, где не хватает контента
        for k, need in allocation.items():
            if available[k] < need:
                deficit[k] = need - available[k]
                allocation[k] = available[k]

        # Распределяем излишки в другие категории
        remaining_pool = [k for k in allocation.keys() if k not in deficit]
        for k, missing in deficit.items():
            for _ in range(missing):
                if not remaining_pool:
                    break
                best = max(remaining_pool, key=lambda x: available[x] - allocation[x])
                allocation[best] += 1
        return allocation

    def schedule_posts(self, total_posts: int = C.DEFAULT_DAILY_POSTS) -> dict[str, list[dict]]:
        """Формирует расписание публикаций на основе доступного контента."""
        time_segment = self._get_time_segment()
        priorities = C.TIME_PRIORITIES[time_segment]

        allocation = self._allocate_slots(total_posts, priorities)
        allocation = self._redistribute_if_needed(allocation)

        # Формируем финальные выборки
        scheduled = {
            "news": random.sample(self.news, min(allocation["news"], len(self.news))),
            "games": random.sample(self.games, min(allocation["games"], len(self.games))),
            "discounts": random.sample(self.discounts, min(allocation["discounts"], len(self.discounts))),
        }
        return scheduled
