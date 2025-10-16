from __future__ import annotations
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from config import constants as C
from models.base import BaseDBModel
# ---------------------------------------------------------------------------------------------------------------------


class PopularityMetrics(BaseModel):
    follows: int = C.ZERO
    hypes: int = C.ZERO
    rating: Optional[float] = Field(None, ge=C.ZERO, le=C.PERCENT_MAX)
    rating_count: int = C.ZERO
    aggregated_rating: Optional[float] = Field(None, ge=C.ZERO, le=C.PERCENT_MAX)
    aggregated_rating_count: int = C.ZERO
    total_rating: Optional[float] = Field(None, ge=C.ZERO, le=C.PERCENT_MAX)
    total_rating_count: Optional[int] = C.ZERO
    popularity: Optional[float] = None


class IGDBMeta(BaseDBModel):
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
    themes: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    artworks: List[str] = Field(default_factory=list)
    game_engines: List[str] = Field(default_factory=list)

    steam_appid: Optional[int] = None
