from typing import Literal
from src.schemas.base import BaseSchema
# ---------------------------------------------------------------------------------------------------------------------


class CheckedEntitySchema(BaseSchema):
    entity_id: int | str
    type: Literal['game', 'news', 'reddit']
    suitable: bool | None = None
    confidence: float | None = None
    reason: str | None = None
