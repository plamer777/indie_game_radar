from datetime import datetime, timedelta
from typing import List, AsyncGenerator
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
        embedding_model: str = C.REDDIT_FILTER_EMBEDDING_MODEL,
        gpt_model: str = C.REDDIT_FILTER_GPT_MODEL,
        prompt_template: str = C.REDDIT_FILTER_PROMPT_TEMPLATE
    ):
        super().__init__(
            open_ai_client, gpt_model, checked_entity_repo = checked_entity_repo,
            embedding_model = embedding_model
        )
        self.time_window = timedelta(hours=time_window_hours)
        self._prompt_template = prompt_template

    async def filter_posts(
        self,
        posts: List[RankedRedditPost],
        game: RankedGameModel
    ) -> AsyncGenerator[RedditPostPublicationSchema, None]:
        now = datetime.now()

        if not self._is_indie_game(game):
            return

        # 1️⃣ Basic filtering by time and minimum metrics
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

    def _has_bad_flair(self, flair: str) -> bool:
        f = flair.lower()
        return any(bad in f for bad in C.REDDIT_FILTER_BAD_FLAIRS)
