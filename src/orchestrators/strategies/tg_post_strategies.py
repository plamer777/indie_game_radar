import random
from datetime import datetime, timedelta, UTC
from src.config import constants as C
from src.schemas import (
    GamePublicationRecordSchema,
    NewsPublicationSchema,
    DiscountPublicationSchema,
    RedditPostPublicationSchema, AllocatedPostsSchema,
)
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class ContentAllocationStrategy:
    """
    Распределяет публикации по источникам с учетом времени суток
    и формирует расписание на весь день (утро → день → вечер).
    """

    def __init__(
        self,
        news: list[NewsPublicationSchema],
        games: list[GamePublicationRecordSchema],
        discounts: list[DiscountPublicationSchema],
        reddit_posts: list[RedditPostPublicationSchema],
        reddit_memes: list[RedditPostPublicationSchema],
    ) -> None:
        self._log = get_logger().bind(service="ContentAllocationStrategy")
        self.news = news or []
        self.games = games or []
        self.discounts = discounts or []
        self.reddit_posts = reddit_posts or []
        self.reddit_memes = reddit_memes or []

    # -------------------------------------------------------------------------
    # --------------------------- ВРЕМЯ И ИНТЕРВАЛЫ ----------------------------
    # -------------------------------------------------------------------------

    def _determine_time_bounds(self) -> tuple[datetime, datetime]:
        """Определяет начало и конец планирования публикаций."""
        now = datetime.now(UTC)
        start_hour, end_hour = C.TIME_WINDOWS["morning"][0], C.TIME_WINDOWS["evening"][1]
        today_start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)

        if now < today_start:
            # если раньше 8 утра — начинаем с 8:00
            start_time = today_start
        elif now >= today_end:
            # если позже 22:00 — переносим на следующий день
            start_time = today_start + timedelta(days=1)
            today_end = today_end + timedelta(days=1)
        else:
            # начинаем с текущего времени + 15 минут
            start_time = now + timedelta(minutes=15)

        return start_time, today_end

    def _split_time_periods(self, start_time: datetime, end_time: datetime) -> list[tuple[str, datetime, datetime]]:
        """Разбивает день на три временных окна (утро, день, вечер)."""
        segments = []
        for name, (start_h, end_h) in C.TIME_WINDOWS.items():
            seg_start = start_time.replace(hour=start_h, minute=0)
            seg_end = start_time.replace(hour=end_h, minute=0)
            if seg_start < start_time:
                seg_start = start_time
            if seg_end > end_time:
                seg_end = end_time
            if seg_start < seg_end:
                segments.append((name, seg_start, seg_end))
        return segments

    # -------------------------------------------------------------------------
    # --------------------------- ЛОГИКА РАСПРЕДЕЛЕНИЯ -------------------------
    # -------------------------------------------------------------------------

    def _allocate_slots(self, total_posts: int, priorities: dict[str, float]) -> dict[str, int]:
        """Рассчитывает, сколько постов выделить под каждую категорию."""
        base_allocation = {k: int(total_posts * v) for k, v in priorities.items()}

        # Корректируем округления
        allocated = sum(base_allocation.values())
        if allocated < total_posts:
            diff = total_posts - allocated
            sorted_keys = sorted(priorities.keys(), key=lambda k: priorities[k], reverse=True)
            for k in sorted_keys[:diff]:
                base_allocation[k] += 1
        return base_allocation

    def _redistribute_if_needed(self, allocation: dict[str, int]) -> dict[str, int]:
        """Если контента не хватает, перераспределяет в пользу других категорий."""
        available = {
            "news": len(self.news),
            "games": len(self.games),
            "discounts": len(self.discounts),
            "reddit_posts": len(self.reddit_posts),
            "reddit_memes": len(self.reddit_memes)
        }

        deficit = {}

        for k, need in allocation.items():
            if available.get(k, 0) < need:
                deficit[k] = need - available[k]
                allocation[k] = available.get(k, 0)

        remaining_pool = [k for k in allocation if k not in deficit]
        for k, missing in deficit.items():
            for _ in range(missing):
                if not remaining_pool:
                    break
                best = max(remaining_pool, key=lambda x: available[x] - allocation[x])
                allocation[best] += 1

        return allocation

    # -------------------------------------------------------------------------
    # --------------------------- ОСНОВНОЙ МЕТОД ------------------------------
    # -------------------------------------------------------------------------

    def schedule_daily_posts(self, total_posts: int = C.DEFAULT_DAILY_POSTS) -> list[AllocatedPostsSchema]:
        """
        Формирует полное расписание публикаций на день.
        Возвращает список с указанием поста и времени публикации.
        """
        start_time, end_time = self._determine_time_bounds()
        segments = self._split_time_periods(start_time, end_time)

        # равномерно делим total_posts по времени суток
        posts_per_segment = total_posts // len(segments)
        leftover = total_posts % len(segments)

        schedule: list[AllocatedPostsSchema] = []
        for i, (segment_name, seg_start, seg_end) in enumerate(segments):
            count = posts_per_segment + (1 if i < leftover else 0)

            priorities = C.TIME_PRIORITIES[segment_name]
            allocation = self._allocate_slots(count, priorities)
            allocation = self._redistribute_if_needed(allocation)

            # Берём контент
            segment_posts: list[AllocatedPostsSchema] = []
            for category, amount in allocation.items():
                pool = getattr(self, category, [])
                if not pool:
                    continue
                selected = random.sample(pool, min(amount, len(pool)))
                for post in selected:
                    segment_posts.append(AllocatedPostsSchema(category=category, post=post))

            # равномерно распределяем по времени внутри сегмента
            if not segment_posts:
                continue

            interval = (seg_end - seg_start) / len(segment_posts)
            for j, entry in enumerate(segment_posts):
                publish_time = seg_start + interval * j
                entry.publish_time = publish_time
                schedule.append(entry)

        # итоговое расписание отсортировано по времени
        schedule.sort(key=lambda x: x.publish_time)
        return schedule
