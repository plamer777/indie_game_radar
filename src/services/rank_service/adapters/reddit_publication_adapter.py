from datetime import timedelta
import numpy as np
from openai import AsyncOpenAI
from src.db.repositories import RedditPostPublicationRepository
from src.mixins import EmbeddingMixin
from src.config import constants as C
from src.schemas import DeduplicationSchema, RedditPostPublicationSchema
# ---------------------------------------------------------------------------------------------------------------------


class RedditPublicationAdapter(EmbeddingMixin):
    def __init__(
        self, open_ai_client: AsyncOpenAI, reddit_publication_repo: RedditPostPublicationRepository,
        model: str = C.REDDIT_FILTER_EMBEDDING_MODEL,
    ) -> None:
        """Initialize the adapter with OpenAI client, news publication repository, and embedding model.

        Args:
            open_ai_client (AsyncOpenAI): The OpenAI client.
            reddit_publication_repo (RedditPostPublicationRepository): The news publication repository.
            model (str, optional): The embedding model name. Defaults to C.NEWS_FILTER_EMBEDDING_MODEL.
        """
        super().__init__(open_ai_client, model)
        self._reddit_publication_repo = reddit_publication_repo

    async def was_published(self, reddit_post: RedditPostPublicationSchema) -> bool:
        """The method checks if the reddit_post was already published.

        Args:
            reddit_post (RedditPostPublicationSchema): The reddit post to check.

        Returns:
            bool: True if the reddit post was published, False otherwise.
        """
        if await self._reddit_publication_repo.was_published(reddit_post):
            return True

        else:
            author_publications = await self._reddit_publication_repo.get_all(
                {
                    'author': reddit_post.author,
                    'created_utc': {
                        '$gte':
                            reddit_post.created_utc - timedelta(days=C.REDDIT_FILTER_DUPLICATION_CHECKING_MAX_AGE_DAYS)
                    }
                },
                generator_mode=True
            )
            embeddings = [
                np.array(publication.embedding) async for publication in author_publications if publication.embedding
            ]
            emb_schema = DeduplicationSchema(
                author=reddit_post.author, title=reddit_post.title, content=reddit_post.selftext,
                embedding=reddit_post.embedding
            )

            return await self._is_duplicated(emb_schema, embeddings=embeddings)
