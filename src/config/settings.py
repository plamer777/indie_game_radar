from __future__ import annotations
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
# ---------------------------------------------------------------------------------------------------------------------
load_dotenv()
# ---------------------------------------------------------------------------------------------------------------------


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__")

    # Mongo
    MONGO_URI: str = Field(..., description="MongoDB connection URI")
    MONGO_DB: str = Field("indie_game_radar", description="Mongo database name")

    # Redis
    REDIS_URL: str = Field("redis://localhost:6379/0")

    # IGDB/Twitch OAuth
    IGDB_CLIENT_ID: str = Field(...)
    IGDB_CLIENT_SECRET: str = Field(...)
    IGDB_BASE_URL: str = Field("https://api.igdb.com/v4")
    TWITCH_OAUTH_URL: str = Field("https://id.twitch.tv/oauth2/token")

    # Steam
    STEAM_STORE_BASE: str = Field("https://store.steampowered.com")
    STEAM_WEBAPI_BASE: str = Field("https://api.steampowered.com")
    STEAM_API_KEY: str = Field(...)

    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram Bot token")
    TELEGRAM_CHAT_ID: str = Field(..., description="Telegram channel/chat id")

    # App behavior
    SCORE_PUBLISH_THRESHOLD: float = Field(0.7)
    RUN_INTERVAL_SECONDS: int = Field(4 * 60 * 60, description="Interval between cycles; if <=0 then single run")
    ONE_SHOT: bool = Field(False, description="Run once and exit when True")

    # HTTP and rate limiting
    HTTP_TIMEOUT_SECONDS: float = Field(15.0)
    STEAM_MAX_CONCURRENCY: int = Field(5)
    IGDB_MAX_CONCURRENCY: int = Field(3)
    HTTP_MAX_RETRIES: int = Field(3)
    HTTP_RETRY_BACKOFF_BASE: float = Field(0.5)
    HTTP_RETRY_BACKOFF_MAX: float = Field(5.0)

    # Caching TTLs (seconds)
    CACHE_TTL_STEAM_DETAILS: int = Field(60 * 60)  # 1 hour
    CACHE_TTL_IGDB_META: int = Field(6 * 60 * 60)  # 6 hours

    # OpenAI
    OPEN_AI_KEY: str = Field(...)
    OPENAI_API_BASE: str = Field("https://api.openai.com/v1")

    # RAWG
    RAWG_API_KEY: str = Field(...)
    RAWG_API_BASE: str = Field("https://api.rawg.io/api")

    # Reddit
    REDDIT_CLIENT_ID: str = Field(...)
    REDDIT_CLIENT_SECRET: str = Field(...)
    REDDIT_USER_AGENT: str = Field(...)
    REDDIT_BASE_URL: str = Field("https://oauth.reddit.com")


settings = Settings()  # evaluated at import time intentionally
