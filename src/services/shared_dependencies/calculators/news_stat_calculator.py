from datetime import datetime
import numpy as np
from src.models.game import NewsStats, SteamNewsItem
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class NewsStatCalculator:

    def compute_news_stats(self, news: list[SteamNewsItem]) -> NewsStats:
        """Aggregates news statistics for a game."""
        timestamps = [int(n.date.timestamp()) for n in news or [] if n.date]

        if not timestamps:
            return NewsStats(
                total_news_last_30d=0,
                total_news_last_90d=0,
                days_since_last_news=None,
                avg_interval_days=None,
            )

        now = datetime.now().timestamp()
        last_news_ts = max(timestamps)
        days_since_last = (now - last_news_ts) / C.SECONDS_IN_DAY

        sorted_ts = sorted(timestamps)
        intervals = (
            np.diff(sorted_ts) / C.SECONDS_IN_DAY if len(sorted_ts) > 1 else []
        )

        total_30d = sum(now - t < C.NEWS_WINDOW_30D * C.SECONDS_IN_DAY for t in timestamps)
        total_90d = sum(now - t < C.NEWS_WINDOW_90D * C.SECONDS_IN_DAY for t in timestamps)

        return NewsStats(
            total_news_last_30d=total_30d,
            total_news_last_90d=total_90d,
            days_since_last_news=round(days_since_last, C.ROUND_PRECISION),
            avg_interval_days=(
                round(np.mean(intervals), C.ROUND_PRECISION) if len(intervals) else None
            ),
        )
