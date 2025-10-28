from datetime import datetime, timedelta
from typing import List, Optional
import numpy as np
from openai import OpenAI
from src.models.game import SteamNewsItem
# ---------------------------------------------------------------------------------------------------------------------


class NewsFilter:
    LOW_VALUE_KEYWORDS = [
        "hotfix", "update", "patch", "version", "dev log", "minor changes",
        "bugfix", "roadmap", "announcement", "delay", "sale", "stream", "podcast"
    ]

    IMPORTANT_KEYWORDS = [
        "release", "launch", "trailer", "new gameplay", "feature",
        "partnership", "publisher", "collaboration", "major update"
    ]

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

    def _contains_low_value_words(self, text: str) -> bool:
        t = text.lower()
        return any(kw in t for kw in self.LOW_VALUE_KEYWORDS)

    def _contains_important_words(self, text: str) -> bool:
        t = text.lower()
        return any(kw in t for kw in self.IMPORTANT_KEYWORDS)

    async def filter_news(
        self,
        news_items: List[SteamNewsItem],
        query: Optional[str] = None
    ) -> List[SteamNewsItem]:
        now = datetime.now()
        filtered = []

        # 1️⃣ фильтр по времени и источникам
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

        # 3️⃣ фильтр по содержанию
        pre_filtered = []
        for item in filtered:
            text = f"{item.title} {item.contents or ''}".lower()
            if self._contains_low_value_words(text) and not self._contains_important_words(text):
                continue
            pre_filtered.append(item)

        # 4️⃣ удаляем дубли по смыслу
        deduped = await self._deduplicate(pre_filtered)

        return deduped

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
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        return float(np.dot(a, b) / denom) if denom else 0.0
