from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from src.config import constants as C
from src.models.base import BaseDBModel
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


class TimeToBeat(BaseModel):
    count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    hastily: Optional[int] = None
    normally: Optional[int] = None
    completely: Optional[int] = None


class IGDBMeta(BaseDBModel):
    igdb_id: int
    name: str
    summary: Optional[str] = None
    storyline: Optional[str] = None
    genres: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)
    release_date: Optional[datetime] = None
    cover_url: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)
    websites: List[str] = Field(default_factory=list)
    metrics: PopularityMetrics = Field(default_factory=PopularityMetrics)
    time_to_beat: Optional[TimeToBeat] = None
    themes: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    artworks: List[str] = Field(default_factory=list)
    game_engines: List[str] = Field(default_factory=list)

    steam_appid: Optional[int] = None
