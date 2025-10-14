from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from config.constants import GAMES_COLLECTION, IGDB_META_COLLECTION, PUBLICATIONS_COLLECTION, APPS_COLLECTION
from db.repositories.base_repo import BaseRepository
from models.game import GameModel, AppModel
from models.igdb import IGDBMeta
from models.publication import PublicationRecord, PublishStatus
from config import constants as C
from schemas import GameSchema
from schemas.igdb_schemas import IGDBMetaSchema
# ---------------------------------------------------------------------------------------------------------------------


class GameRepository(BaseRepository[GameModel]):
    def __init__(
        self, collection_name: str = GAMES_COLLECTION,
        model: type[BaseModel] | None = GameModel,
        db: AsyncIOMotorDatabase | None = None
    ):
        super().__init__(collection_name, model, db)

    async def upsert_game(self, data: GameSchema | list[GameSchema]) -> None:
        if isinstance(data, list):
            data = [item.model_dump() for item in data]
        else:
            data = [data.model_dump()]
        for game in data:
            params = {"steam_appid": game.steam_appid, 'deleted_at': None}
            existing = await self._collection.find_one(params)
            if existing:
                game.pop('updated_at', None)
                await self._collection.update_one(
                    params,
                    {"$set": game}
                )
            else:
                await self._collection.insert_one(game)

    async def get_by_appid(self, appid: int) -> Optional[GameModel]:
        doc = await self._collection.find_one({"steam_appid": appid})
        return self._adapter.validate_python(doc) if doc else None

    async def get_unpublished_candidates(self, limit: int = C.UNPUBLISHED_QUERY_LIMIT_DEFAULT) -> List[GameModel]:
        pipeline = [
            {
                "$lookup": {
                    "from": "publications",
                    "let": {"appid": "$steam_appid"},
                    "pipeline": [
                        {"$match": {"$expr": {"$and": [
                            {"$eq": ["$steam_appid", "$$appid"]},
                            {"$eq": ["$status", "published"]},
                        ]}}},
                        {"$limit": C.LOOKUP_LIMIT_ONE}
                    ],
                    "as": "pub"
                }
            },
            {"$match": {"pub": {"$size": C.ZERO}}},
            {"$sort": {"last_score": C.DESC, "updated_at": C.DESC}},
            {"$limit": limit}
        ]
        docs = [d async for d in self._collection.aggregate(pipeline)]
        return [self._adapter.validate_python(d) for d in docs]

    async def update_score(self, appid: int, score: float) -> None:
        await self._collection.update_one(
            {"steam_appid": appid},
            {"$set": {"last_score": score, "last_ranked_at": datetime.utcnow(), "updated_at": datetime.utcnow()}}
        )


class IGDBRepository(BaseRepository[IGDBMeta]):
    def __init__(
        self, collection_name: str = IGDB_META_COLLECTION,
        model: type[BaseModel] | None = IGDBMeta,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)

    async def upsert_meta(self, meta: IGDBMetaSchema) -> None:
        data = meta.model_dump()
        created_at = data.pop("created_at", None)
        updated_at = data.pop("updated_at", None)
        await self._collection.update_one(
            {"igdb_id": meta.igdb_id},
            {"$set": data, "$setOnInsert": {"created_at": created_at, "updated_at": updated_at}},
            upsert=True,
        )

    async def get_by_igdb_id(self, igdb_id: int) -> Optional[IGDBMeta]:
        doc = await self._collection.find_one({"igdb_id": igdb_id})
        return self._adapter.validate_python(doc) if doc else None

    async def link_to_appid(self, igdb_id: int, steam_appid: int) -> None:
        await self._collection.update_one(
            {"igdb_id": igdb_id},
            {"$set": {"steam_appid": steam_appid, "updated_at": datetime.utcnow()}}
        )


class PublicationRepository(BaseRepository[PublicationRecord]):
    def __init__(
        self, collection_name: str = PUBLICATIONS_COLLECTION, model: type[PublicationRecord] = PublicationRecord,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)


    async def mark_published(self, record: PublicationRecord) -> None:
        data = record.model_dump()
        data["status"] = PublishStatus.published
        data["updated_at"] = datetime.utcnow()
        await self._collection.update_one(
            {"steam_appid": record.steam_appid, "channel": record.channel},
            {"$set": data, "$setOnInsert": {"created_at": record.created_at}},
            upsert=True,
        )

    async def mark_failed(self, record: PublicationRecord, error: str) -> None:
        data = record.model_dump()
        data["status"] = PublishStatus.failed
        data["error"] = error
        data["attempt"] = data.get("attempt", 0) + 1
        data["updated_at"] = datetime.utcnow()
        await self._collection.update_one(
            {"steam_appid": record.steam_appid, "channel": record.channel},
            {"$set": data, "$setOnInsert": {"created_at": record.created_at}},
            upsert=True,
        )

    async def was_published(self, steam_appid: int, channel: str = "telegram") -> bool:
        doc = await self._collection.find_one({"steam_appid": steam_appid, "channel": channel, "status":
            PublishStatus.published})
        return doc is not None


class AppRepository(BaseRepository[AppModel]):
    def __init__(
        self, collection_name: str = APPS_COLLECTION, model: type[AppModel] = AppModel,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)
