from datetime import timedelta
import numpy as np
from openai import AsyncOpenAI
from src.db.repositories import NewsPublicationRepository
from src.mixins import EmbeddingMixin
from src.config import constants as C
from src.models.game import SteamNewsItem
from src.schemas import DeduplicationSchema, NewsPublicationSchema
# ---------------------------------------------------------------------------------------------------------------------


class NewsPublicationAdapter(EmbeddingMixin):
    def __init__(
        self, open_ai_client: AsyncOpenAI, news_publication_repo: NewsPublicationRepository,
        model: str = C.NEWS_FILTER_EMBEDDING_MODEL,
    ) -> None:
        """Initialize the adapter with OpenAI client, news publication repository, and embedding model.

        Args:
            open_ai_client (AsyncOpenAI): The OpenAI client.
            news_publication_repo (NewsPublicationRepository): The news publication repository.
            model (str, optional): The embedding model name. Defaults to C.NEWS_FILTER_EMBEDDING_MODEL.
        """
        super().__init__(open_ai_client, model)
        self._news_publication_repo = news_publication_repo

    async def was_published(self, news: NewsPublicationSchema) -> bool:
        """The method checks if the news was already published.

        Args:
            news (SteamNewsItem): The news to check.

        Returns:
            bool: True if the news was published, False otherwise.
        """
        if await self._news_publication_repo.was_published(news.gid):
            return True

        else:
            author_publications = await self._news_publication_repo.get_all(
                {
                    'author': news.author,
                    'date': {'$gte': news.date - timedelta(days=C.NEWS_FILTER_DUPLICATION_CHECKING_MAX_AGE_DAYS)}
                },
                generator_mode=True
            )
            embeddings = [
                np.array(publication.embedding) async for publication in author_publications if publication.embedding
            ]
            emb_schema = DeduplicationSchema(
                author=news.author, title=news.title, content=news.contents, embedding=news.embedding
            )

            return await self._is_duplicated(emb_schema, embeddings=embeddings)
