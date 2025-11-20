from __future__ import annotations
from typing import Optional
from datetime import datetime
from enum import StrEnum
from pydantic import Field, BaseModel
from src.config import constants as C
from src.models.base import BaseDBModel
from src.models.game import PriceInfo, SteamExtendedInfo, PlatformsInfo, ReviewItem
from src.models.speedrun import CategoryLeader


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
    error: Optional[str] = None
    name: str
    supported_languages: Optional[str] = None
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None
    release_date: Optional[datetime] = None
    is_coming_soon: Optional[bool] = True
    genres: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    developers: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)
    website: Optional[str] = None
    header_image: Optional[str] = None
    background: Optional[str] = None
    screenshots: list[str] = Field(default_factory=list)
    price: Optional[PriceInfo] = None
    is_free: bool = False
    ext_info: Optional[SteamExtendedInfo] = None
    platforms: PlatformsInfo = Field(default_factory=PlatformsInfo)
    recommendations: Optional[int] = None
    categories: list[str] = Field(default_factory=list)


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
    embedding: Optional[list[float]] = None


class DiscountPublication(BaseDBModel):
    steam_appid: str
    name: str
    detailed_description: Optional[str] = None
    short_description: Optional[str] = None
    header_image: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
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


class RedditPostPublication(BaseDBModel):
    reddit_id: str
    channel: str = C.DEFAULT_TELEGRAM_CHANNEL
    status: PublishStatus = PublishStatus.pending
    message_id: Optional[str] = None
    attempt: int = 0
    error: Optional[str] = None
    title: str
    selftext: Optional[str] = None
    selftext_html: Optional[str] = None
    url: Optional[str] = None
    permalink: Optional[str] = None
    domain: Optional[str] = None
    author: Optional[str] = None
    author_fullname: Optional[str] = None
    author_premium: Optional[bool] = None
    subreddit: Optional[str] = None
    subreddit_type: Optional[str] = None
    subreddit_subscribers: Optional[int] = None
    created_utc: datetime
    edited_utc: Optional[datetime] = None
    score: Optional[int] = None
    ups: Optional[int] = None
    downs: Optional[int] = None
    upvote_ratio: Optional[float] = None
    num_comments: Optional[int] = None
    num_crossposts: Optional[int] = None
    preview_images: Optional[list[str]] = None
    media_urls: Optional[list[str]] = None
    total_awards_received: Optional[int] = None
    all_awardings: Optional[list[str]] = None
    post_hint: Optional[str] = None
    link_flair_text: Optional[str] = None
    extract_snippet: Optional[str] = None
    embedding: Optional[list[float]] = None


class ReviewSummary(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    sentiment_score: Optional[float] = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    common_requests: list[str] = []
    notable_quotes: list[str] = []
    surprises: list[str] = []
    confidence: Optional[str] = None


class ReviewPublication(BaseDBModel):
    channel: str = C.DEFAULT_TELEGRAM_CHANNEL
    status: PublishStatus = PublishStatus.pending
    message_id: Optional[str] = None
    attempt: int = 0
    error: Optional[str] = None
    steam_appid: int
    game_name: str
    image: Optional[str] = None
    total_reviews: Optional[int]
    total_negative: Optional[int]
    total_positive: Optional[int]
    review_score: Optional[int]
    ratio: Optional[float]
    reviews: list[ReviewItem]
    summary: Optional[ReviewSummary] = None


class GameLeaderboardPublication(BaseDBModel):
    channel: str = C.DEFAULT_TELEGRAM_CHANNEL
    status: PublishStatus = PublishStatus.pending
    message_id: Optional[str] = None
    attempt: int = 0
    error: Optional[str] = None
    steam_appid: int | None = None
    game_name: str
    release_date: datetime
    weblink: str
    discord: str | None = None
    category_leaderboards: list[CategoryLeader] = []
    leaders_hash: str | None = None
