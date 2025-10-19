from __future__ import annotations
from typing import Optional
from src.config import constants as C
from src.models.publication import PublishStatus
from src.schemas.base import BaseSchema
# ---------------------------------------------------------------------------------------------------------------------


class PublicationRecordSchema(BaseSchema):
    steam_appid: int
    channel: str = C.DEFAULT_TELEGRAM_CHANNEL
    status: PublishStatus = PublishStatus.pending
    message_id: Optional[str] = None
    attempt: int = 0
    score_at_publish: Optional[float] = None
    error: Optional[str] = None
