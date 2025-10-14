from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import StrEnum
from config import constants as C


class PublishStatus(StrEnum):
    pending = "pending"
    published = "published"
    failed = "failed"


class PublicationRecord(BaseModel):
    steam_appid: int
    channel: str = C.DEFAULT_TELEGRAM_CHANNEL
    status: PublishStatus = PublishStatus.pending
    message_id: Optional[str] = None
    attempt: int = 0
    score_at_publish: Optional[float] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
