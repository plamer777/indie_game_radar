from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.models.base import BaseDBModel
# ---------------------------------------------------------------------------------------------------------------------


class RedditPost(BaseDBModel):
    reddit_id: str = Field(..., description="Post ID (e.g. '1oc22gq')")
    fullname: Optional[str] = Field(None, description="Fullname (e.g. t3_1oc22gq)")
    steam_appid: Optional[int] = Field(None, description="Steam AppID if it can be extracted from the link")
    game_name: Optional[str] = Field(None, description="Game name if extracted manually or via mapping")
    type: str | None = None
    title: str = Field(..., description="Post title")
    selftext: Optional[str] = Field(None, description="Post text (for self-posts)")
    selftext_html: Optional[str] = Field(None, description="HTML version of the text if available")
    url: Optional[str] = Field(None, description="URL the post points to, or the article site")
    permalink: Optional[str] = Field(None, description="Permanent Reddit link (e.g. https://reddit.com/…)")
    domain: Optional[str] = Field(None, description="Link domain (e.g. store.steampowered.com)")

    author: Optional[str] = Field(None, description="Author name (u/name)")
    author_fullname: Optional[str] = Field(None, description="Author fullname (e.g. t2_xxx)")
    author_is_blocked: Optional[bool] = Field(None, description="True if the author is blocked")
    author_premium: Optional[bool] = Field(None, description="True if the author has Reddit Premium")

    subreddit: str = Field(..., description="Subreddit name (e.g. 'IndieGaming')")
    subreddit_id: Optional[str] = Field(None, description="Subreddit ID (e.g. t5_2r0e3)")
    subreddit_name_prefixed: Optional[str] = Field(None, description="Example: 'r/IndieGaming'")
    subreddit_type: Optional[str] = Field(None, description="Subreddit type: public/private etc.")
    subreddit_subscribers: Optional[int] = Field(None, description="Subreddit subscriber count if available")

    created_utc: datetime = Field(..., description="Creation time (utc)")
    edited_utc: Optional[datetime] = Field(None, description="Edit time, if edited")

    score: int = Field(..., description="Score (upvotes-downvotes)")
    ups: Optional[int] = Field(None, description="Up-vote count (if available)")
    downs: Optional[int] = Field(None, description="Down-vote count (if available)")
    upvote_ratio: Optional[float] = Field(None, description="Ratio of up-votes to total votes")

    num_comments: int = Field(..., description="Comment count")
    num_crossposts: Optional[int] = Field(None, description="Crosspost count (if available)")

    over_18: bool = Field(..., description="True if the post is NSFW")
    is_self: bool = Field(..., description="True if self-post (text)")
    is_video: bool = Field(..., description="True if video post")
    is_original_content: Optional[bool] = Field(None, description="True if content is marked as original")

    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    thumbnail_height: Optional[int] = Field(None, description="Thumbnail height if present")
    thumbnail_width: Optional[int] = Field(None, description="Thumbnail width if present")

    preview_images: Optional[List[str]] = Field(None, description="List of preview image/gif URLs")
    media_urls: Optional[List[str]] = Field(None, description="Media resource links (secure_media, media_embed, etc.)")

    total_awards_received: Optional[int] = Field(None, description="Total number of awards given to the post")
    all_awardings: Optional[List[Dict[str, Any]]] = Field(None, description="Award details (list of dicts)")

    post_hint: Optional[str] = Field(None, description="Post format hint (e.g. 'link', 'image', 'video')")
    link_flair_text: Optional[str] = Field(None, description="Link flair text")
    link_flair_template_id: Optional[str] = Field(None, description="Link flair template ID")

    extract_snippet: Optional[str] = Field(None, description="Short excerpt from selftext suitable for quoting")

    crawl_time: datetime = Field(default_factory=datetime.now, description="Time the record was downloaded/saved")

    class Config:
        from_attributes = True


class RankedRedditPost(RedditPost):
    last_score: Optional[float] = None
    last_ranked_at: Optional[datetime] = None
