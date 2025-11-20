from datetime import datetime
from pydantic import BaseModel, field_validator, Field, AliasPath, AliasChoices
from src.models.base import BaseDBModel
# ---------------------------------------------------------------------------------------------------------------------


class Category(BaseModel):
    id: str
    name: str
    weblink: str
    type: str
    rules: str
    players: dict | None = None


class Player(BaseModel):
    id: str
    name: str = Field(validation_alias=AliasChoices(AliasPath('names', 'international'), 'name'))
    weblink: str
    role: str | None = None


class Result(BaseModel):
    place: int
    videos: list[str] = []
    weblink: str
    comment: str | None = None
    date: datetime
    times: dict = {}
    player: Player


    @field_validator('videos', mode='before')
    def validate_videos(cls, v):
        if type(v) is list:
            return v
        videos = v.get('links', [])
        return [video.get('uri') for video in videos if video.get('uri')]


class CategoryLeader(BaseModel):
    weblink: str
    category: Category
    result: Result


class GameLeaderboard(BaseDBModel):
    steam_appid: int | None = None
    weblink: str
    discord: str | None = None
    category_leaderboards: list[CategoryLeader] = []
