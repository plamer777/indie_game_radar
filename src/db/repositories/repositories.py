from __future__ import annotations
from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from src.config.constants import GAMES_COLLECTION, IGDB_META_COLLECTION, GAME_PUBLICATIONS_COLLECTION, APPS_COLLECTION, \
    GAME_SNAPSHOTS_COLLECTION, NEWS_PUBLICATIONS_COLLECTION
from src.db.repositories.base_repo import BaseRepository
from src.models.game import GameModel, AppModel, GameSnapshot
from src.models import IGDBMeta
from src.models.publication import GamePublicationRecord, PublishStatus, NewsPublicationRecord
# ---------------------------------------------------------------------------------------------------------------------


class GameRepository(BaseRepository[GameModel]):
    def __init__(
        self, collection_name: str = GAMES_COLLECTION,
        model: type[BaseModel] | None = GameModel,
        db: AsyncIOMotorDatabase | None = None
    ):
        super().__init__(collection_name, model, db)

    async def update_score(self, appid: int, score: float) -> None:
        await self._collection.update_one(
            {"steam_appid": appid},
            {"$set": {"last_score": score, "last_ranked_at": datetime.now(), "updated_at": datetime.now()}}
        )


class IGDBRepository(BaseRepository[IGDBMeta]):
    def __init__(
        self, collection_name: str = IGDB_META_COLLECTION,
        model: type[BaseModel] | None = IGDBMeta,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)

    async def get_by_igdb_id(self, igdb_id: int) -> Optional[IGDBMeta]:
        doc = await self._collection.find_one({"igdb_id": igdb_id})
        return self._adapter.validate_python(doc) if doc else None

    async def link_to_appid(self, igdb_id: int, steam_appid: int) -> None:
        await self._collection.update_one(
            {"igdb_id": igdb_id},
            {"$set": {"steam_appid": steam_appid, "updated_at": datetime.now()}}
        )


class GamePublicationRepository(BaseRepository[GamePublicationRecord]):
    def __init__(
        self, collection_name: str = GAME_PUBLICATIONS_COLLECTION, model: type[GamePublicationRecord] = GamePublicationRecord,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)


    async def mark_published(self, record: GamePublicationRecord) -> None:
        data = record.model_dump()
        data["status"] = PublishStatus.published
        data["updated_at"] = datetime.now()
        await self.add_or_update(data, search_field="steam_appid")

    async def mark_failed(self, record: GamePublicationRecord, error: str) -> None:
        data = record.model_dump()
        data["status"] = PublishStatus.failed
        data["error"] = error
        data["attempt"] = data.get("attempt", 0) + 1
        data["updated_at"] = datetime.now()
        await self.add_or_update(data, search_field="steam_appid")

    async def was_published(self, steam_appid: int, channel: str = "telegram") -> bool:
        doc = await self._collection.find_one(
            {"steam_appid": steam_appid, "channel": channel, "status": PublishStatus.published}
        )
        return doc is not None


class GameSnapshotRepository(BaseRepository[GameSnapshot]):
    def __init__(
        self, collection_name: str = GAME_SNAPSHOTS_COLLECTION, model: type[GameSnapshot] = GameSnapshot,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)



class AppRepository(BaseRepository[AppModel]):
    def __init__(
        self, collection_name: str = APPS_COLLECTION, model: type[AppModel] = AppModel,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)


class NewsPublicationRepository(BaseRepository[NewsPublicationRecord]):
    def __init__(
        self, collection_name: str = NEWS_PUBLICATIONS_COLLECTION,
        model: type[NewsPublicationRecord] = NewsPublicationRecord,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)

    async def mark_published(self, record: NewsPublicationRecord) -> None:
        data = record.model_dump()
        data["status"] = PublishStatus.published
        data["updated_at"] = datetime.now()
        await self.add_or_update(data, search_field="gid")

    async def mark_failed(self, record: NewsPublicationRecord, error: str) -> None:
        data = record.model_dump()
        data["status"] = PublishStatus.failed
        data["error"] = error
        data["attempt"] = data.get("attempt", 0) + 1
        data["updated_at"] = datetime.now()
        await self.add_or_update(data, search_field="gid")

    async def was_published(self, gid: str, channel: str = "telegram") -> bool:
        doc = await self._collection.find_one(
            {"gid": gid, "channel": channel, "status": PublishStatus.published}
        )
        return doc is not None