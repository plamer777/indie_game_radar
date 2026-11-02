from typing import Optional
from pydantic import BaseModel
# ---------------------------------------------------------------------------------------------------------------------


class Author(BaseModel):
    name: Optional[str]
    fullname: Optional[str] = None
    is_blocked: bool = False
    is_gold: bool = False


class Subreddit(BaseModel):
    display_name: str
    subscribers: Optional[int] = None
    id: Optional[str] = None
    name_prefixed: Optional[str] = None
    type: str = "public"


class Submission(BaseModel):
    id: str
    name: str
    title: str
    selftext: Optional[str]
    selftext_html: Optional[str]
    url: str
    permalink: str
    domain: str
    author: Author
    subreddit: Subreddit
    subreddit_id: Optional[str]
    subreddit_name_prefixed: str
    subreddit_type: str
    created_utc: float
    edited: Optional[float]
    score: int
    ups: int
    downs: int
    upvote_ratio: Optional[float]
    num_comments: int
    num_crossposts: Optional[int]
    over_18: bool
    is_self: bool
    is_video: bool
    is_original_content: Optional[bool]
    thumbnail: Optional[str]
    thumbnail_height: Optional[int]
    thumbnail_width: Optional[int]
    preview: Optional[dict]
    media: Optional[dict]
