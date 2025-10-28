from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from src.config import constants as C
from src.models.base import BaseDBModel
# ---------------------------------------------------------------------------------------------------------------------


class AppModel(BaseDBModel):
    appid: int
    name: str
    status: str
    last_modified: datetime | None = None
    price_change_number: int = 0


class NewsStats(BaseModel):
    total_news_last_30d: int
    total_news_last_90d: int
    days_since_last_news: Optional[float]
    avg_interval_days: Optional[float]


class SteamNewsItem(BaseModel):
    gid: str = Field(..., description="Уникальный идентификатор новости в Steam")
    title: str = Field(..., description="Заголовок новости")
    url: Optional[str] = Field(None, description="URL новости (часто ведет на внешний ресурс)")
    is_external_url: bool = Field(False, description="Флаг, указывает внешний ли источник")
    author: Optional[str] = Field(None, description="Автор публикации")
    contents: Optional[str] = Field(None, description="HTML содержимое новости")
    feedlabel: Optional[str] = Field(None, description="Отображаемое название источника (например, PCGamesN)")
    feedname: Optional[str] = Field(None, description="Системное имя фида")
    feed_type: Optional[int] = Field(None, description="Тип фида (0 = обычный, 1 = RSS и т.д.)")
    appid: int = Field(..., description="Steam AppID игры, к которой относится новость")
    date: datetime = Field(..., description="Дата публикации в формате datetime")
    score: Optional[float] = Field(None, description="Оценка новости")
    last_ranked_at: Optional[datetime] = Field(None, description="Дата последнего ранжирования")
    relevance: Optional[float] = Field(None, description="Релевантность новости")


class PriceInfo(BaseModel):
    currency: str = Field(..., min_length=C.CURRENCY_CODE_LEN, max_length=C.CURRENCY_CODE_LEN)
    initial: float = Field(..., ge=C.ZERO)
    final: float = Field(..., ge=C.ZERO)
    discount_percent: float = Field(C.ZERO, ge=C.ZERO, le=C.PERCENT_MAX)


class PriceOption(BaseModel):
    price_in_cents_with_discount: int
    percent_savings: int
    percent_savings_text: Optional[str]
    option_text: Optional[str]
    packageid: Optional[int]
    is_free_license: Optional[bool]


class PackageGroup(BaseModel):
    name: Optional[str]
    display_type: Optional[int]
    subs: List[PriceOption]


class PlatformsInfo(BaseModel):
    linux: bool = False
    mac: bool = False
    windows: bool = False


class GameModel(BaseDBModel):
    steam_appid: int = Field(..., ge=C.MIN_STEAM_APPID)
    name: str
    supported_languages: Optional[str] = None
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None
    release_date: Optional[datetime] = None
    is_coming_soon: Optional[bool] = True
    genres: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    developers: List[str] = Field(default_factory=list)
    publishers: List[str] = Field(default_factory=list)
    website: Optional[str] = None
    header_image: Optional[str] = None
    background: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)
    price: Optional[PriceInfo] = None
    is_free: bool = False
    ext_info: Optional[SteamExtendedInfo] = None
    platforms: PlatformsInfo = Field(default_factory=PlatformsInfo)
    recommendations: Optional[int] = None
    categories: List[str] = Field(default_factory=list)

    package_groups: List[PackageGroup] = Field(default_factory=list)
    last_news: List[SteamNewsItem] = Field(default_factory=list)

    igdb_id: Optional[int] = None



class RankedGameModel(GameModel):
    last_score: Optional[float] = None
    last_ranked_at: Optional[datetime] = None


class GameSnapshot(BaseDBModel):
    steam_appid: int
    snapshot_time: datetime
    price: Optional[float]
    discount_percent: Optional[float]
    current_players: Optional[int]
    review_ratio: Optional[float]
    total_achievements: Optional[int]
    avg_unlock_percent: Optional[float]
    avg_days_per_news: Optional[float]


class CurrentPlayersResponse(BaseModel):
    player_count: int


class AchievementPct(BaseModel):
    name: str
    percent: float


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
    total_negative: Optional[int]
    total_positive: Optional[int]
    review_score: Optional[int]
    ratio: Optional[float]
    reviews: List[ReviewItem]
    cursor: Optional[str]  # если пагинация


# Возможная расширенная модель игры, объединяющая с твоим GameModel:
class SteamExtendedInfo(BaseModel):
    steam_appid: int
    current_players: Optional[int]
    achievements: Optional[list[AchievementPct]]
    review_summary: Optional[ReviewResponse]
    news_stats: Optional[NewsStats] = None
