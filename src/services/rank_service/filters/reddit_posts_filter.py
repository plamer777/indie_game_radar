from datetime import datetime, timedelta
from typing import List
import numpy as np
import re
from openai import OpenAI
from src.models import RankedGameModel
from src.models.reddit import RedditPost, RankedRedditPost
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class RedditPostFilter:

    def __init__(
        self,
        open_ai_client: OpenAI,
        time_window_hours: int = C.REDDIT_FILTER_TIME_WINDOW_HOURS,
        similarity_threshold: float = C.REDDIT_FILTER_SIMILARITY_THRESHOLD,
        embedding_model: str = "text-embedding-3-small"
    ):
        self._client = open_ai_client
        self.time_window = timedelta(hours=time_window_hours)
        self.similarity_threshold = similarity_threshold
        self.embedding_model = embedding_model

    async def _get_embedding(self, text: str) -> np.ndarray:
        if not text.strip():
            return np.zeros(1536)
        response = await self._client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return np.array(response.data[0].embedding)

    async def filter_posts(
        self,
        posts: List[RankedRedditPost],
        game: RankedGameModel
    ) -> List[RankedRedditPost]:
        now = datetime.now()
        result = []

        # 1️⃣ Базовая фильтрация по времени и минимальным метрикам
        for p in posts:
            if (now - p.created_at) > self.time_window:
                continue
            if p.last_score < C.REDDIT_FILTER_MIN_RANK_SCORE:
                continue
            text_len = len((p.selftext or "").strip())
            if text_len < C.REDDIT_FILTER_MIN_CONTENT_LENGTH:
                continue
            if p.link_flair_text and self._has_bad_flair(p.link_flair_text):
                continue
            result.append(p)

        # 2️⃣ Проверка релевантности игре (если указана)
        result = await self._filter_by_relevance(result, game)

        # 3️⃣ Сортировка: сначала по дате, потом по рейтингу
        result.sort(key=lambda p: (p.created_at, p.rank_score), reverse=True)
        return result

    async def _filter_by_relevance(
        self, posts: List[RedditPost], game: RankedGameModel
    ) -> List[RankedRedditPost]:
        """
        Проверяет релевантность постов игре:
          1️⃣ если есть ссылка на Steam с appid — пропускаем без проверки эмбеддингов
          2️⃣ если в названии игры ≥ 3 слов — считаем эмбеддинговую близость
          3️⃣ остальные посты отбрасываются
        """
        filtered = []
        game_tokens = re.findall(r"[a-zA-Z0-9]+", game.name.lower())
        use_embedding = len(game_tokens) >= 3

        # заранее вычисляем эмбеддинг игры (только если нужно)
        game_emb = None
        if use_embedding:
            game_emb = await self._get_embedding(game.name)

        steam_pattern = re.compile(r"store\.steampowered\.com/app/(\d+)", re.IGNORECASE)

        for p in posts:
            # 1️⃣ проверка наличия appid в ссылке
            url = (p.url or "") + " " + (p.selftext or "")
            match = steam_pattern.search(url)
            if match:
                try:
                    found_appid = int(match.group(1))
                    if game.steam_appid and found_appid == game.steam_appid:
                        p.relevance = 1.0
                        filtered.append(p)
                        continue
                except ValueError:
                    pass

            # 2️⃣ проверка по эмбеддингу (если игра достаточно уникальна)
            if use_embedding and game_emb is not None:
                text = f"{p.title} {p.selftext or ''}"
                emb = await self._get_embedding(text)
                sim = self._cosine_similarity(game_emb, emb)
                if sim >= self.similarity_threshold:
                    p.relevance = round(sim, 3)
                    filtered.append(p)

        return filtered

    def _has_bad_flair(self, flair: str) -> bool:
        f = flair.lower()
        return any(bad in f for bad in C.REDDIT_FILTER_BAD_FLAIRS)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        return float(np.dot(a, b) / denom) if denom else 0.0
