from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from src.config import constants as C
from src.config.settings import settings
# ---------------------------------------------------------------------------------------------------------------------


def get_database(uri: str = settings.MONGO_URI, db_name: str = C.MONGO_DB) -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(uri, uuidRepresentation="standard")
    return getattr(client, db_name)
