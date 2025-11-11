from src.models.base import BaseDBModel
# ---------------------------------------------------------------------------------------------------------------------


class CheckedEntity(BaseDBModel):
    entity_id: int | str
    type: str
    suitable: bool | None = None
    confidence: float | None = None
    reason: str | None = None