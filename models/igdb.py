from __future__ import annotations
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class PopularityMetrics(BaseModel):
    follows: int = C.ZERO
    hypes: int = C.ZERO
    rating: Optional[float] = Field(None, ge=C.ZERO, le=C.PERCENT_MAX)
    rating_count: int = C.ZERO
    aggregated_rating: Optional[float] = Field(None, ge=C.ZERO, le=C.PERCENT_MAX)
    aggregated_rating_count: int = C.ZERO
    popularity: Optional[float] = None


class IGDBMeta(BaseModel):
    igdb_id: int
    name: str
    summary: Optional[str] = None
    storyline: Optional[str] = None
    genres: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)
    release_date: Optional[datetime] = None
    cover_url: Optional[HttpUrl] = None
    screenshots: List[HttpUrl] = Field(default_factory=list)
    websites: List[HttpUrl] = Field(default_factory=list)
    metrics: PopularityMetrics = Field(default_factory=PopularityMetrics)

    steam_appid: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
