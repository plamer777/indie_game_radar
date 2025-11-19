from datetime import datetime
from pydantic import BaseModel, field_validator
from src.models.base import BaseDBModel
# ---------------------------------------------------------------------------------------------------------------------


class Category(BaseModel):
    id: int
    name: str
    weblink: str
    type: str
    rules: str
    players: dict


class Result(BaseModel):
    place: int
    videos: list[str]
    weblink: str
    comment: str
    date: datetime
    times: dict
    players: list[str]

    @field_validator('players', mode='before')
    def validate_players(cls, v):
        return [player.get('id') for player in v if player.get('id')]

    @field_validator('videos', mode='before')
    def validate_videos(cls, v):
        videos = v.get('links', [])
        return [video.get('uri') for video in videos if video.get('uri')]


class CategoryLeaderboard(BaseModel):
    level: str
    weblink: str
    category: Category
    results: list[Result]


class Record(BaseDBModel):
    steam_appid: int
    game_name: str
    weblink: str
    discord: str
