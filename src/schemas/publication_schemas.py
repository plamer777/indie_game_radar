from __future__ import annotations
from datetime import datetime
from typing import Optional, Union
from pydantic import Field
from typing_extensions import Literal
from src.config import constants as C
from src.models.game import PriceInfo, SteamExtendedInfo, PlatformsInfo
from src.models.publication import PublishStatus
from src.schemas.base import BaseSchema
# ---------------------------------------------------------------------------------------------------------------------


class GamePublicationRecordSchema(BaseSchema):
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


class NewsPublicationSchema(BaseSchema):
    gid: str
    title: str
    channel: str = C.DEFAULT_TELEGRAM_CHANNEL
    status: PublishStatus = PublishStatus.pending
    url: Optional[str] = None
    author: Optional[str] = None
    contents: str
    header_image: Optional[str] = None
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


class DiscountPublicationSchema(BaseSchema):
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


class RedditPostPublicationSchema(BaseSchema):
    reddit_id: str
    channel: str = C.DEFAULT_TELEGRAM_CHANNEL
    status: PublishStatus = PublishStatus.pending
    message_id: Optional[str] = None
    attempt: int = 0
    error: Optional[str] = None
    title: str
    steam_appid: Optional[int] = None
    type: Literal['game_related', 'game_dev_story', 'meme']
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


class AllocatedPostsSchema(BaseSchema):
    category: str
    post: Union[
        GamePublicationRecordSchema, NewsPublicationSchema, DiscountPublicationSchema, RedditPostPublicationSchema
    ]
    publish_time: datetime | None = None
