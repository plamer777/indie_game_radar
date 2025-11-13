from datetime import datetime, timedelta
from typing import List, AsyncGenerator
import numpy as np
import re
from openai import AsyncOpenAI
from src.db.repositories import CheckedEntityRepository
from src.models import RankedGameModel
from src.models.reddit import RankedRedditPost
from src.config import constants as C
from src.schemas import RedditPostPublicationSchema, DeduplicationSchema
from src.services.rank_service.filters.base_filter import BaseFilter
# ---------------------------------------------------------------------------------------------------------------------


class RedditPostFilter(BaseFilter):

    def __init__(
        self,
        open_ai_client: AsyncOpenAI,
        checked_entity_repo: CheckedEntityRepository,
        time_window_hours: int = C.REDDIT_FILTER_TIME_WINDOW_HOURS,
        similarity_threshold: float = C.REDDIT_FILTER_SIMILARITY_THRESHOLD,
        embedding_model: str = C.REDDIT_FILTER_EMBEDDING_MODEL,
        gpt_model: str = C.REDDIT_FILTER_GPT_MODEL,
        prompt_template: str = C.REDDIT_FILTER_PROMPT_TEMPLATE
    ):
        super().__init__(
            open_ai_client, gpt_model, checked_entity_repo = checked_entity_repo,
            embedding_model = embedding_model
        )
        self.time_window = timedelta(hours=time_window_hours)
        self.similarity_threshold = similarity_threshold
        self._prompt_template = prompt_template

    async def filter_posts(
        self,
        posts: List[RankedRedditPost],
        game: RankedGameModel
    ) -> AsyncGenerator[RedditPostPublicationSchema, None]:
        now = datetime.now()

        if not self._is_indie_game(game):
            return

        # 1️⃣ Базовая фильтрация по времени и минимальным метрикам
        for p in posts:
            if (now - p.created_utc) > self.time_window:
                continue
            if p.last_score < C.REDDIT_FILTER_MIN_RANK_SCORE:
                continue
            text_len = len((p.selftext or "").strip())
            if text_len < C.REDDIT_FILTER_MIN_CONTENT_LENGTH:
                continue
            if p.link_flair_text and self._has_bad_flair(p.link_flair_text):
                continue

            prompt = self._prompt_template.format(game_name=game.name, title=p.title, text=p.selftext)
            pub_schema = RedditPostPublicationSchema(**p.model_dump())
            emb_schema = DeduplicationSchema(author=p.author, title=p.title, content=p.selftext)
            if await self._is_content_valid(pub_schema, emb_schema, prompt, 'reddit'):
                yield pub_schema

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
