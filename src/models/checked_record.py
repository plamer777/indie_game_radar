from src.models.base import BaseDBModel
# ---------------------------------------------------------------------------------------------------------------------


class CheckedEntity(BaseDBModel):
    entity_id: int
    type: str
    suitable: bool
    confidence: float
    reason: str