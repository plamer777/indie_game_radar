from __future__ import annotations
from pydantic import Field, HttpUrl, field_validator
from typing import Optional, List
from datetime import datetime
from models.igdb import PopularityMetrics
from schemas.base import BaseSchema
# ---------------------------------------------------------------------------------------------------------------------


class IGDBMetaSchema(BaseSchema):
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
    artworks: List[HttpUrl] = Field(default_factory=list)
    game_engines: List[str] = Field(default_factory=list)

    steam_appid: Optional[int] = None

    @field_validator('cover_url', mode='before')
    def validate_cover_url(cls, v):
        if v and not v.startswith('http'):
            return 'https:' + v
        return v

    @field_validator('screenshots', 'websites', 'artworks', mode='before')
    def validate_screenshots(cls, v: list[str]):
        v = [s  if s.startswith('http') else 'https:' + s for s in v]
        return v