from typing import Literal, Optional
from src.schemas.base import BaseSchema
# ---------------------------------------------------------------------------------------------------------------------


class CheckedEntitySchema(BaseSchema):
    entity_id: int | str
    type: Literal['game', 'news', 'reddit']
    suitable: bool | None = None
    confidence: float | None = None
    reason: str | None = None


class DeduplicationSchema(BaseSchema):
    title: str
    content: str
    author: Optional[str] = None
