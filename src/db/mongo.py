from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from src.config import constants as C
from src.config import settings
# ---------------------------------------------------------------------------------------------------------------------


def get_database(uri: str = settings.MONGO_URI, db_name: str = settings.MONGO_DB) -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(uri, uuidRepresentation="standard")
    return getattr(client, db_name)


async def ensure_indexes() -> None:
    db = get_database()
    await db.games.create_index([("steam_appid", C.ASC)], unique=True)
    await db.games.create_index([("last_score", C.DESC)])
    await db.games.create_index([("updated_at", C.DESC)])
    await db.games.create_index([("is_free", C.ASC)])
    await db.games.create_index([("price.final", C.ASC)])
    await db.games.create_index([("last_score", C.DESC), ("updated_at", C.DESC)])

    await db.igdb_meta.create_index([("igdb_id", C.ASC)], unique=True)
    await db.igdb_meta.create_index([("steam_appid", C.ASC)])
    await db.igdb_meta.create_index([("updated_at", C.DESC)])
    await db.igdb_meta.create_index([("metrics.popularity", C.DESC)])

    await db.publications.create_index([("steam_appid", C.ASC), ("channel", C.ASC)], unique=True)
    await db.publications.create_index([("status", C.ASC), ("updated_at", C.DESC)])
