from datetime import datetime
from pydantic import Field
from src.models.speedrun import CategoryLeader
from src.schemas.base import BaseSchema
# ---------------------------------------------------------------------------------------------------------------------


class GameLeaderboardSchema(BaseSchema):
    """The schema represents a leaderboard of a game"""
    steam_appid: int | None = None
    release_date: datetime = Field(validation_alias='release-date')
    weblink: str
    discord: str | None = None
    category_leaderboards: list[CategoryLeader] = []
