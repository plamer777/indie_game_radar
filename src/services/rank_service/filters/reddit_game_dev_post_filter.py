from datetime import datetime, timedelta
from typing import List
from openai import AsyncOpenAI
from src.models.reddit import RankedRedditPost
from src.config import constants as C
from src.services.rank_service.filters.base_filter import BaseFilter
# ---------------------------------------------------------------------------------------------------------------------


class RedditDevPostFilter(BaseFilter):
    """
    Фильтр для постов, связанных с геймдевом, но не с конкретной игрой.
    """

    def __init__(
        self,
        open_ai_client: AsyncOpenAI,
        time_window_days: int = C.REDDIT_DEV_FILTER_TIME_WINDOW_DAYS,
        gpt_model: str = C.REDDIT_DEV_FILTER_GPT_MODEL,
        prompt_template: str = C.REDDIT_DEV_FILTER_PROMPT_TEMPLATE,
    ):
        super().__init__(open_ai_client, gpt_model)
        self.time_window = timedelta(days=time_window_days)
        self._prompt_template = prompt_template

    async def filter_posts(self, posts: List[RankedRedditPost]) -> List[RankedRedditPost]:
        now = datetime.now()
        result = []

        for p in posts:
            # 1️⃣ базовые проверки
            if (now - p.created_at) > self.time_window:
                continue
            if p.last_score < C.REDDIT_DEV_FILTER_MIN_RANK_SCORE:
                continue
            if len((p.selftext or "").strip()) < C.REDDIT_DEV_FILTER_MIN_CONTENT_LENGTH:
                continue
            if p.link_flair_text and self._has_bad_flair(p.link_flair_text):
                continue

            # 2️⃣ контент-фильтр GPT
            prompt = self._prompt_template.format(
                title=p.title,
                text=p.selftext
            )
            content_filter = await self._filter_by_content(prompt)
            if not content_filter.get("suitable"):
                continue

            result.append(p)

        # сортировка по свежести и score
        result.sort(key=lambda p: (p.created_at, p.rank_score), reverse=True)
        return result

    # --- helpers ---
    def _has_bad_flair(self, flair: str) -> bool:
        f = flair.lower()
        return any(bad in f for bad in C.REDDIT_DEV_FILTER_BAD_FLAIRS)
