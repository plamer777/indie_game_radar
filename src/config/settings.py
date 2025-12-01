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

    # IGDB/Twitch OAuth
    IGDB_CLIENT_ID: str = Field(...)
    IGDB_CLIENT_SECRET: str = Field(...)

    # Steam
    STEAM_API_KEY: str = Field(...)

    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram Bot token")
    TELEGRAM_CHAT_ID: str = Field(..., description="Telegram channel/chat id")

    # OpenAI
    OPEN_AI_KEY: str = Field(...)

    # Reddit
    REDDIT_CLIENT_ID: str = Field(...)
    REDDIT_CLIENT_SECRET: str = Field(...)
    REDDIT_USER_AGENT: str = Field(...)

    TELETHON_API_ID: int = Field(...)
    TELETHON_API_HASH: str = Field(...)
    SOURCE_CHANNEL_USERNAME: str = Field(...)
    TARGET_BOT_USERNAME: str = Field(...)


settings = Settings()  # evaluated at import time intentionally
