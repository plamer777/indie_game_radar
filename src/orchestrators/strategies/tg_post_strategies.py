import random
from datetime import datetime, timedelta, UTC
from src.config import constants as C
from src.schemas import (
    GamePublicationRecordSchema,
    NewsPublicationSchema,
    DiscountPublicationSchema,
    RedditPostPublicationSchema, AllocatedPostsSchema, ReviewPublicationSchema, GameLeaderboardPublicationSchema,
)
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class ContentAllocationStrategy:
    """
    Distributes publications across sources based on the time of day
    and builds a schedule for the whole day (morning → day → evening).
    """

    def __init__(
        self,
        news: list[NewsPublicationSchema],
        games: list[GamePublicationRecordSchema],
        discounts: list[DiscountPublicationSchema],
        reddit_posts: list[RedditPostPublicationSchema],
        reddit_memes: list[RedditPostPublicationSchema],
        reviews: list[ReviewPublicationSchema],
        game_leaderboards: list[GameLeaderboardPublicationSchema],
    ) -> None:
        self._log = get_logger().bind(service="ContentAllocationStrategy")
        self._news = news or []
        self._games = games or []
        self._discounts = discounts or []
        self._reddit_posts = reddit_posts or []
        self._reddit_memes = reddit_memes or []
        self._reviews = reviews or []
        self._game_leaderboards = game_leaderboards or []

    @property
    def game_leaderboards(self) -> list[GameLeaderboardPublicationSchema]:
        """The list of game leaderboards to be published."""
        return self._game_leaderboards

    @property
    def news(self) -> list[NewsPublicationSchema]:
        """The list of news to be published."""
        return self._news

    @property
    def games(self) -> list[GamePublicationRecordSchema]:
        """The list of games to be published."""
        return self._games

    @property
    def discounts(self) -> list[DiscountPublicationSchema]:
        """The list of discounts to be published."""
        return self._discounts

    @property
    def reddit_posts(self) -> list[RedditPostPublicationSchema]:
        """The list of reddit posts to be published."""
        return self._reddit_posts

    @property
    def reddit_memes(self) -> list[RedditPostPublicationSchema]:
        """The list of reddit memes to be published."""
        return self._reddit_memes

    @property
    def reviews(self) -> list[ReviewPublicationSchema]:
        """The list of reviews to be published."""
        return self._reviews

    # -------------------------------------------------------------------------
    # --------------------------- TIME AND INTERVALS ---------------------------
    # -------------------------------------------------------------------------

    def _determine_time_bounds(self) -> tuple[datetime, datetime]:
        """Determines the start and end of the publication scheduling window."""
        now = datetime.now(UTC)
        start_hour, end_hour = C.TIME_WINDOWS["morning"][0], C.TIME_WINDOWS["evening"][1]
        today_start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)

        if now < today_start:
            # if earlier than 8 AM — start at 8:00
            start_time = today_start
        elif now >= today_end:
            # if later than 22:00 — move to the next day
            start_time = today_start + timedelta(days=1)
            today_end = today_end + timedelta(days=1)
        else:
            # start from current time + 15 minutes
            start_time = now + timedelta(minutes=15)

        return start_time, today_end

    def _split_time_periods(self, start_time: datetime, end_time: datetime) -> list[tuple[str, datetime, datetime]]:
        """Splits the day into three time windows (morning, day, evening)."""
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
    # --------------------------- ALLOCATION LOGIC -------------------------
    # -------------------------------------------------------------------------

    def _allocate_slots(self, total_posts: int, priorities: dict[str, float]) -> dict[str, int]:
        """Computes how many posts to allocate to each category."""
        base_allocation = {k: int(total_posts * v) for k, v in priorities.items()}

        # Fix rounding
        allocated = sum(base_allocation.values())
        if allocated < total_posts:
            diff = total_posts - allocated
            sorted_keys = sorted(priorities.keys(), key=lambda k: priorities[k], reverse=True)
            for k in sorted_keys[:diff]:
                base_allocation[k] += 1
        return base_allocation

    def _redistribute_if_needed(self, allocation: dict[str, int]) -> dict[str, int]:
        """If there is not enough content, redistributes to other categories."""
        available = {
            "news": len(self._news),
            "games": len(self._games),
            "discounts": len(self._discounts),
            "reddit_posts": len(self._reddit_posts),
            "reddit_memes": len(self._reddit_memes),
            "reviews": len(self._reviews),
            "game_leaderboards": len(self._game_leaderboards)
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
    # --------------------------- MAIN METHOD ------------------------------
    # -------------------------------------------------------------------------

    def schedule_daily_posts(self, total_posts: int = C.DEFAULT_DAILY_POSTS) -> list[AllocatedPostsSchema]:
        """
        Builds the full publication schedule for the day.
        Returns a list of posts with their publish times.
        """
        start_time, end_time = self._determine_time_bounds()
        segments = self._split_time_periods(start_time, end_time)

        # evenly split total_posts across the time windows
        posts_per_segment = total_posts // len(segments)
        leftover = total_posts % len(segments)

        schedule: list[AllocatedPostsSchema] = []
        for i, (segment_name, seg_start, seg_end) in enumerate(segments):
            count = posts_per_segment + (1 if i < leftover else 0)

            priorities = C.TIME_PRIORITIES[segment_name]
            allocation = self._allocate_slots(count, priorities)
            allocation = self._redistribute_if_needed(allocation)

            # Take the content
            segment_posts: list[AllocatedPostsSchema] = []
            for category, amount in allocation.items():
                pool = getattr(self, category, [])
                if not pool:
                    continue
                selected = random.sample(pool, min(amount, len(pool)))
                for post in selected:
                    if post in pool:
                        pool.remove(post)
                    segment_posts.append(AllocatedPostsSchema(category=category, post=post))

            # distribute evenly across time within the segment
            if not segment_posts:
                continue

            interval = (seg_end - seg_start) / len(segment_posts)
            for j, entry in enumerate(segment_posts):
                publish_time = seg_start + interval * j
                entry.publish_time = publish_time
                schedule.append(entry)

        # final schedule sorted by time
        schedule.sort(key=lambda x: x.publish_time)
        return schedule
