from datetime import datetime, timedelta
from typing import List, Optional
import numpy as np
from openai import OpenAI
from src.models.game import SteamNewsItem
# ---------------------------------------------------------------------------------------------------------------------


class NewsFilter:
    def __init__(
        self,
        open_ai_client: OpenAI,
        time_window_hours: int = 24,
        allowed_feeds: Optional[List[str]] = None,
        blocked_feeds: Optional[List[str]] = None,
        similarity_threshold: float = 0.75,
        embedding_model: str = "text-embedding-3-small"
    ):
        self.time_window = timedelta(hours=time_window_hours)
        self.allowed_feeds = set(allowed_feeds or [])
        self.blocked_feeds = set(blocked_feeds or [])
        self.similarity_threshold = similarity_threshold
        self.embedding_model = embedding_model
        self._open_ai_client = open_ai_client

    async def _get_embedding(self, text: str) -> np.ndarray:
        if not text.strip():
            return np.zeros(1536)
        response = await self._open_ai_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return np.array(response.data[0].embedding)

    async def filter_news(
        self,
        news_items: List[SteamNewsItem],
        query: Optional[str] = None
    ) -> List[SteamNewsItem]:
        """
       The method filters news items based on time, source, relevance, and duplicates.

       Args:
           news_items: List of news items to filter.
           query: Optional query string to filter by relevance.
       Returns:
           List of filtered news items.
        """
        now = datetime.now()
        filtered = []

        # 1️⃣ фильтр по времени
        for item in news_items:
            if (now - item.date) > self.time_window:
                continue
            if self.allowed_feeds and item.feedlabel not in self.allowed_feeds:
                continue
            if item.feedlabel in self.blocked_feeds:
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

        # 3️⃣ удаляем дубли по смыслу
        filtered = await self._deduplicate(filtered)

        return filtered

    async def _deduplicate(self, items: List[SteamNewsItem]) -> List[SteamNewsItem]:
        unique = []
        seen_embeddings = []
        for item in items:
            emb = await self._get_embedding(f"{item.title} {item.contents or ''}")
            if all(self._cosine_similarity(emb, e) < 0.92 for e in seen_embeddings):
                unique.append(item)
                seen_embeddings.append(emb)
        return unique

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
