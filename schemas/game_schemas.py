from __future__ import annotations
from pydantic import BaseModel, Field, HttpUrl, field_validator, AliasPath
from typing import Optional, List, Literal
from datetime import datetime
from config import constants as C
from models.game import PlatformsInfo, PackageGroup
from schemas.base import BaseSchema
# ---------------------------------------------------------------------------------------------------------------------


class AppSchema(BaseSchema):
    appid: int
    name: str
    status: Literal['new', 'updated', 'deleted'] = 'new'
    last_modified: datetime | None = None
    price_change_number: int = 0


class PriceInfoSchema(BaseModel):
    currency: str = Field(..., min_length=C.CURRENCY_CODE_LEN, max_length=C.CURRENCY_CODE_LEN)
    initial: float = Field(..., ge=C.ZERO)
    final: float = Field(..., ge=C.ZERO)
    discount_percent: float = Field(C.ZERO, ge=C.ZERO, le=C.PERCENT_MAX)


class ReviewStats(BaseModel):
    total: int = Field(C.ZERO, ge=C.ZERO)
    positive: int = Field(C.ZERO, ge=C.ZERO)
    ratio: float = Field(0.0, ge=C.RATIO_MIN, le=C.RATIO_MAX)


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
    screenshots: List[HttpUrl] = Field(default_factory=list, validation_alias=AliasPath('path_thumbnail'))
    price: Optional[PriceInfoSchema] = None
    reviews: ReviewStats = Field(default_factory=ReviewStats)
    is_free: bool = False
    ext_info: Optional[SteamExtendedInfo] = None
    platforms: PlatformsInfo = Field(default_factory=PlatformsInfo)

    package_groups: List[PackageGroup] = Field(default_factory=list)

    recommendations: Optional[int] = Field(None, validation_alias=AliasPath('total'))
    last_score: Optional[float] = None
    last_ranked_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    igdb_id: Optional[int] = None

    @field_validator('genres', mode='before')
    def _normalize_genres(cls, value: list[dict | str]) -> list[str]:
        if type(value) is dict:
            return [g.get('description') for g in value]

        return value


class GameSnapshotSchema(BaseSchema):
    steam_appid: int
    snapshot_time: datetime = Field(default_factory=datetime.now)
    price: Optional[float]
    discount_percent: Optional[int]
    current_players: Optional[int]
    review_ratio: Optional[float]
    achievements_pct: Optional[dict[str, float]]
    news_count: Optional[int]


class CurrentPlayersResponseSchema(BaseSchema):
    player_count: int


class AchievementPct(BaseModel):
    name: str
    percent: float


class AchievementStatsResponse(BaseModel):
    achievements: List[AchievementPct]


class ReviewAuthor(BaseModel):
    steamid: Optional[str]
    num_games_owned: Optional[int]
    num_reviews: Optional[int]
    played_for: Optional[float]


class ReviewItem(BaseModel):
    author: ReviewAuthor
    review: Optional[str]
    language: Optional[str]
    timestamp_created: Optional[int]
    voted_up: Optional[bool]
    votes_up: Optional[int]
    votes_funny: Optional[int]


class ReviewResponse(BaseModel):
    total_reviews: Optional[int]
    reviews: List[ReviewItem]
    cursor: Optional[str]  # если пагинация


# Возможная расширенная модель игры, объединяющая с твоим GameModel:
class SteamExtendedInfo(BaseModel):
    steam_appid: int
    current_players: Optional[int]
    achievements: Optional[AchievementStatsResponse]
    review_summary: Optional[ReviewResponse]
