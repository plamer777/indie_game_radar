from __future__ import annotations
from typing import Optional
from datetime import datetime
from enum import StrEnum
from src.config import constants as C
from src.models.base import BaseDBModel
# ---------------------------------------------------------------------------------------------------------------------


class PublishStatus(StrEnum):
    pending = "pending"
    published = "published"
    failed = "failed"


class GamePublicationRecord(BaseDBModel):
    steam_appid: int
    channel: str = C.DEFAULT_TELEGRAM_CHANNEL
    status: PublishStatus = PublishStatus.pending
    message_id: Optional[str] = None
    attempt: int = 0
    score_at_publish: Optional[float] = None
    error: Optional[str] = None


class NewsPublicationRecord(BaseDBModel):
    gid: str
    title: str
    channel: str = C.DEFAULT_TELEGRAM_CHANNEL
    status: PublishStatus = PublishStatus.pending
    url: Optional[str] = None
    author: Optional[str] = None
    contents: str
    feedlabel: Optional[str] = None
    appid: int
    date: datetime
    score: Optional[float]
    last_ranked_at: Optional[datetime] = None
    relevance: Optional[float] = None
    message_id: Optional[str] = None
    attempt: int = 0
    error: Optional[str] = None


class DiscountPublication(BaseDBModel):
    game_id: str
    old_price: float
    new_price: float
    channel: str = C.DEFAULT_TELEGRAM_CHANNEL
    status: PublishStatus = PublishStatus.pending
    percent_drop: float
    absolute_drop: float
    detected_at: datetime
    message_id: Optional[str] = None
    attempt: int = 0
    error: Optional[str] = None
