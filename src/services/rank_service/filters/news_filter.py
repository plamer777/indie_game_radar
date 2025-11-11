from datetime import datetime, timedelta
from typing import List, Optional
import numpy as np
from openai import AsyncOpenAI
from src.db.repositories.repositories import CheckedEntityRepository
from src.models.game import SteamNewsItem, RankedGameModel
from src.config import constants as C
from src.schemas import DeduplicationSchema
from src.services.rank_service.filters.base_filter import BaseFilter
# ---------------------------------------------------------------------------------------------------------------------


class NewsFilter(BaseFilter):

    def __init__(
        self,
        open_ai_client: AsyncOpenAI,
        checked_entity_repo: CheckedEntityRepository,
        time_window_hours: int = C.NEWS_FILTER_TIME_WINDOW_HOURS,
        allowed_feeds: Optional[List[str]] = None,
        blocked_feeds: Optional[List[str]] = None,
        similarity_threshold: float = C.NEWS_FILTER_SIMILARITY_THRESHOLD,
        embedding_model: str = C.NEWS_FILTER_EMBEDDING_MODEL,
        gpt_model: str = C.NEWS_FILTER_GPT_MODEL,
        prompt_template: str = C.NEWS_FILTER_PROMPT_TEMPLATE,
    ):
        super().__init__(
            open_ai_client, gpt_model, checked_entity_repo=checked_entity_repo, embedding_model=embedding_model
        )
        self.time_window = timedelta(hours=time_window_hours)
        self.allowed_feeds = set(allowed_feeds or [])
        self.blocked_feeds = set(blocked_feeds or [])
        self.similarity_threshold = similarity_threshold
        self._prompt_template = prompt_template

    def _contains_low_value_words(self, text: str) -> bool:
        t = text.lower()
        return any(kw in t for kw in C.NEWS_FILTER_LOW_VALUE_KEYWORDS)

    def _contains_important_words(self, text: str) -> bool:
        t = text.lower()
        return any(kw in t for kw in C.NEWS_FILTER_IMPORTANT_KEYWORDS)

    async def filter_news(
        self,
        news_items: List[SteamNewsItem],
        game: RankedGameModel,
        query: Optional[str] = None
    ) -> List[SteamNewsItem]:
        now = datetime.now()
        filtered = []

        if not self._is_indie_game(game):
            return filtered

        # 1️⃣ фильтр по времени и источникам
        for item in news_items:
            if (now - item.date) > self.time_window:
                continue
            if self.allowed_feeds and item.feedlabel not in self.allowed_feeds:
                continue
            if item.feedlabel in self.blocked_feeds:
                continue
            if item.score < C.NEWS_FILTER_MIN_SCORE:
                continue
            filtered.append(item)

        # 2️⃣ фильтр по релевантности (если есть query)
        if query:
            query_emb = await self._get_embedding(query)
            results = []
            for item in filtered:
                text = f"{item.title} {item.contents or ''}"
                emb = await self._get_embedding(text)
                sim = self._cosine_similarity(query_emb, emb)
                if sim >= self.similarity_threshold:
                    item.relevance = round(sim, 3)
                    results.append(item)
            filtered = sorted(results, key=lambda x: x.relevance, reverse=True)

        # 3️⃣ фильтр по содержанию
        deduplicated = []
        for item in filtered:
            text = f"{item.title} {item.contents or ''}".lower()
            if self._contains_low_value_words(text) and not self._contains_important_words(text):
                continue

            # 4️⃣ удаляем дубли по смыслу
            if not await self._is_deduplicated(
                DeduplicationSchema(author=item.author, title=item.title, content=item.contents)
            ):
                checked = await self._get_checked(entity_id=item.gid, entity_type='news')
                if checked:
                    if checked.suitable:
                        deduplicated.append(item)
                    continue

                prompt = self._prompt_template.format(game_name=game.name, title=item.title, text=item.contents)
                content_filter = await self._filter_by_content(prompt)
                await self._add_to_checked(entity_id=item.gid, entity_type='news', result=content_filter)
                if content_filter["suitable"]:
                    deduplicated.append(item)

        return deduplicated
