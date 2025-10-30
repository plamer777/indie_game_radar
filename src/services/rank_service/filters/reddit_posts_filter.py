from datetime import datetime, timedelta
from typing import List
import numpy as np
import re
from openai import OpenAI
from src.models import RankedGameModel
from src.models.reddit import RankedRedditPost
from src.config import constants as C
from src.services.rank_service.filters.base_filter import BaseFilter
# ---------------------------------------------------------------------------------------------------------------------


class RedditPostFilter(BaseFilter):

    def __init__(
        self,
        open_ai_client: OpenAI,
        time_window_hours: int = C.REDDIT_FILTER_TIME_WINDOW_HOURS,
        similarity_threshold: float = C.REDDIT_FILTER_SIMILARITY_THRESHOLD,
        embedding_model: str = C.REDDIT_FILTER_EMBEDDING_MODEL,
        gpt_model: str = C.REDDIT_FILTER_GPT_MODEL,
        prompt_template: str = C.REDDIT_FILTER_PROMPT_TEMPLATE
    ):
        super().__init__(open_ai_client, gpt_model)
        self.time_window = timedelta(hours=time_window_hours)
        self.similarity_threshold = similarity_threshold
        self.embedding_model = embedding_model
        self._prompt_template = prompt_template

    async def _get_embedding(self, text: str) -> np.ndarray:
        if not text.strip():
            return np.zeros(1536)
        response = await self._open_ai_client.embeddings.create(
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

        if not self._is_indie_game(game):
            return result

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
            prompt = self._prompt_template.format(game_name=game.name, title=p.title, text=p.selftext)
            content_filter = await self._filter_by_content(prompt)
            if not content_filter["suitable"]:
                continue

            result.append(p)

        # 3️⃣ Сортировка: сначала по дате, потом по рейтингу
        result.sort(key=lambda p: (p.created_at, p.rank_score), reverse=True)
        return result

    async def _filter_by_relevance(
        self, posts: List[RankedRedditPost], game: RankedGameModel
    ) -> List[RankedRedditPost]:
        """
        Проверяет релевантность постов игре:
          1️⃣ если есть ссылка на Steam с appid — пропускаем без проверки эмбеддингов
          2️⃣ если в названии игры ≥ 3 слов — считаем эмбеддинговую близость
          3️⃣ остальные посты отбрасываются
        """
        filtered = []

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

        return filtered

    def _has_bad_flair(self, flair: str) -> bool:
        f = flair.lower()
        return any(bad in f for bad in C.REDDIT_FILTER_BAD_FLAIRS)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        return float(np.dot(a, b) / denom) if denom else 0.0
