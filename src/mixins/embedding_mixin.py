import numpy as np
from openai import AsyncOpenAI
from src.config import constants as C
from src.schemas import DeduplicationSchema
# ---------------------------------------------------------------------------------------------------------------------


class EmbeddingMixin:
    """The mixin for embedding generation and duplication detection."""
    def __init__(self, open_ai_client: AsyncOpenAI, embedding_model: str) -> None:
        """Initialize the mixin with OpenAI client and embedding model.
        :param open_ai_client: The OpenAI client.
        :param embedding_model: The embedding model name.
        """
        self._open_ai_client = open_ai_client
        self._embedding_model = embedding_model
        self._seen_embeddings: list[np.ndarray] = []

    async def _get_item_embedding(self, item: DeduplicationSchema) -> np.ndarray:
        """Get the embedding for the given item.
        :param item: The item to get the embedding for.
        :return: The embedding for the given item.
        """
        return await self._get_embedding(f"{item.author or ''} {item.title} {item.content or ''}")

    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get the embedding for the given text.
        :param text: The text to get the embedding for.
        :return: The embedding for the given text.
        """
        if not text.strip():
            return np.zeros(1536)
        response = await self._open_ai_client.embeddings.create(
            model=self._embedding_model,
            input=text
        )
        return np.array(response.data[0].embedding)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate the cosine similarity between two embeddings.
        :param a: The first embedding.
        :param b: The second embedding.
        :return: The cosine similarity between the two embeddings.
        """
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        return float(np.dot(a, b) / denom) if denom else 0.0

    async def _is_duplicated(
        self, item: DeduplicationSchema, threshold: float = C.DEFAULT_DUPLICATION_THRESHOLD,
        embeddings: list[np.ndarray] = None
    ) -> bool:
        """Check if the given item is duplicated.
        :param item: The item to check.
        :param threshold: The threshold for duplication detection.
        :return: True if the item is duplicated, False otherwise.
        """
        embeddings = embeddings or self._seen_embeddings
        emb = item.embedding or await self._get_embedding(f"{item.author or ''} {item.title} {item.content or ''}")
        item.embedding = emb.tolist()
        if not embeddings:
            embeddings.append(emb)
            return False
        elif all(self._cosine_similarity(emb, e) < threshold for e in embeddings):
            embeddings.append(emb)
            return False

        return True
