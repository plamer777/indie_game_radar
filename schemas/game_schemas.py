from __future__ import annotations
from pydantic import Field, HttpUrl, field_validator, AliasPath
from typing import Optional, List, Literal
from datetime import datetime
from config import constants as C
from models.game import PlatformsInfo, PackageGroup, PriceInfo, SteamExtendedInfo, SteamNewsItem
from schemas.base import BaseSchema
# ---------------------------------------------------------------------------------------------------------------------


class AppSchema(BaseSchema):
    appid: int
    name: str
    status: Literal['new', 'updated', 'deleted'] = 'new'
    last_modified: datetime | None = None
    price_change_number: int = 0


class GameSchema(BaseSchema):
    steam_appid: int = Field(..., ge=C.MIN_STEAM_APPID)
    name: str
    supported_languages: Optional[str] = None
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None
    release_date: Optional[datetime] = None
    genres: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    developers: List[str] = Field(default_factory=list)
    publishers: List[str] = Field(default_factory=list)
    website: Optional[HttpUrl] = None
    header_image: Optional[HttpUrl] = None
    background: Optional[HttpUrl] = None
    screenshots: List[HttpUrl] = Field(default_factory=list)
    price: Optional[PriceInfo] = None
    is_free: bool = False
    ext_info: Optional[SteamExtendedInfo] = None
    platforms: PlatformsInfo = Field(default_factory=PlatformsInfo)
    categories: List[str] = Field(default_factory=list)
    package_groups: List[PackageGroup] = Field(default_factory=list)
    last_news: List[SteamNewsItem] = Field(default_factory=list)

    recommendations: Optional[int] = Field(None, validation_alias=AliasPath('recommendations', 'total'))
    last_score: Optional[float] = None
    last_ranked_at: Optional[datetime] = None

    igdb_id: Optional[int] = None

    @field_validator('genres', mode='before')
    def _normalize_genres(cls, value: list[dict | str]) -> list[str]:
        if type(value) is list:
            try:
                return [g.get('description') for g in value if g.get('description')]
            except Exception:
                pass

        return value

    @field_validator('screenshots', mode='before')
    def _normalize_screenshots(cls, value: list[dict | str]) -> list[str]:
        if type(value) is list:
            try:
                return [s.get('path_full') for s in value if s.get('path_full')]
            except Exception:
                pass

        return value


class GameSnapshotSchema(BaseSchema):
    steam_appid: int
    snapshot_time: datetime = Field(default_factory=datetime.now)
    price: Optional[float]
    discount_percent: Optional[float]
    current_players: Optional[int]
    review_ratio: Optional[float]
    total_achievements: Optional[int]
    avg_unlock_percent: Optional[float]
    avg_days_per_news: Optional[float]
