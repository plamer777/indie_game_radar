from __future__ import annotations
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from src.config.constants import GAMES_COLLECTION, IGDB_META_COLLECTION, GAME_PUBLICATIONS_COLLECTION, APPS_COLLECTION, \
    GAME_SNAPSHOTS_COLLECTION, NEWS_PUBLICATIONS_COLLECTION, DISCOUNT_PUBLICATIONS_COLLECTION, RANKED_GAMES_COLLECTION, \
    REDDIT_POSTS_COLLECTION, RANKED_REDDIT_POSTS_COLLECTION, CHECKED_ENTITIES_COLLECTION, \
    REDDIT_PUBLICATIONS_COLLECTION, REVIEW_PUBLICATIONS_COLLECTION, LEADERBOARD_COLLECTION, \
    GAME_LEADERBOARD_PUBLICATIONS_COLLECTION
from src.db.repositories.base_repo import BaseRepository
from src.models.game import GameModel, AppModel, GameSnapshot, RankedGameModel
from src.models import IGDBMeta, RedditPost, RankedRedditPost, CheckedEntity, GameLeaderboard
from src.models.publication import GamePublicationRecord, PublishStatus, NewsPublicationRecord, DiscountPublication, \
    RedditPostPublication, ReviewPublication, GameLeaderboardPublication
from src.config import constants as C
from src.schemas import GamePublicationRecordSchema, NewsPublicationSchema, RedditPostPublicationSchema, \
    DiscountPublicationSchema, GameLeaderboardPublicationSchema


# ---------------------------------------------------------------------------------------------------------------------


class GameRepository(BaseRepository[GameModel]):
    def __init__(
        self, collection_name: str = GAMES_COLLECTION,
        model: type[GameModel] | None = GameModel,
        db: AsyncIOMotorDatabase | None = None
    ):
        super().__init__(collection_name, model, db)


class RankedGameRepository(BaseRepository[RankedGameModel]):
    def __init__(
        self, collection_name: str = RANKED_GAMES_COLLECTION,
        model: type[RankedGameModel] | None = RankedGameModel,
        db: AsyncIOMotorDatabase | None = None
    ):
        super().__init__(collection_name, model, db)


class RedditPostRepository(BaseRepository[RedditPost]):
    def __init__(
        self, collection_name: str = REDDIT_POSTS_COLLECTION,
        model: type[RedditPost] | None = RedditPost,
        db: AsyncIOMotorDatabase | None = None
    ):
        super().__init__(collection_name, model, db)


class RankedRedditPostRepository(BaseRepository[RankedRedditPost]):
    def __init__(
        self, collection_name: str = RANKED_REDDIT_POSTS_COLLECTION,
        model: type[RankedRedditPost] | None = RankedRedditPost,
        db: AsyncIOMotorDatabase | None = None
    ):
        super().__init__(collection_name, model, db)


class IGDBRepository(BaseRepository[IGDBMeta]):
    def __init__(
        self, collection_name: str = IGDB_META_COLLECTION,
        model: type[BaseModel] | None = IGDBMeta,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)


class LeaderboardRepository(BaseRepository[GameLeaderboard]):
    def __init__(
        self, collection_name: str = LEADERBOARD_COLLECTION,
        model: type[GameLeaderboard] | None = GameLeaderboard,
        db: AsyncIOMotorDatabase | None = None
    ):
        super().__init__(collection_name, model, db)


class GamePublicationRepository(BaseRepository[GamePublicationRecord]):
    def __init__(
        self, collection_name: str = GAME_PUBLICATIONS_COLLECTION, model: type[GamePublicationRecord] = GamePublicationRecord,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)

    async def mark_published(self, record: GamePublicationRecordSchema, search_field: str = 'steam_appid') -> None:
        await super().mark_published(record, search_field=search_field)

    async def mark_failed(
        self, record: GamePublicationRecordSchema, error: str, search_field: str = 'steam_appid'
    ) -> None:
        await super().mark_failed(record, error, search_field=search_field)

    async def was_published(self, steam_appid: int, channel: str = "telegram") -> bool:
        doc = await self._collection.find_one(
            {"steam_appid": steam_appid, "channel": channel, "status": PublishStatus.published}
        )
        return doc is not None


class GameLeaderboardPublicationRepository(BaseRepository[GameLeaderboardPublication]):
    def __init__(
        self, collection_name: str = GAME_LEADERBOARD_PUBLICATIONS_COLLECTION,
        model: type[GameLeaderboardPublication] = GameLeaderboardPublication,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)

    async def mark_published(self, record: GameLeaderboardPublicationSchema, search_field: str = 'steam_appid') -> None:
        await super().mark_published(record, search_field=search_field)

    async def mark_failed(
        self, record: GameLeaderboardPublicationSchema, error: str, search_field: str = 'steam_appid'
    ) -> None:
        await super().mark_failed(record, error, search_field=search_field)

    async def was_published(
        self, record: GameLeaderboardPublicationSchema, channel: str = "telegram"
    ) -> bool:
        """The method checks if the leaderboard was published.
        :param record: The leaderboard publication record.
        :param channel: The channel to check for.
        :return: True if the leaderboard was published, False otherwise.
        """
        doc = await self._collection.find_one(
            {
                "steam_appid": record.steam_appid,
                "leaders_hash": record.leaders_hash,
                "channel": channel, "status": PublishStatus.published
            }
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


class ReviewPublicationRepository(BaseRepository[ReviewPublication]):
    def __init__(
        self, collection_name: str = REVIEW_PUBLICATIONS_COLLECTION, model: type[ReviewPublication] = ReviewPublication,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)

    async def mark_published(self, record: GamePublicationRecordSchema, search_field: str = 'steam_appid') -> None:
        await super().mark_published(record, search_field=search_field)

    async def mark_failed(
        self, record: GamePublicationRecordSchema, error: str, search_field: str = 'steam_appid'
    ) -> None:
        await super().mark_failed(record, error, search_field=search_field)

    async def was_published(self, steam_appid: int, channel: str = "telegram") -> bool:
        doc = await self._collection.find_one(
            {"steam_appid": steam_appid, "channel": channel, "status": PublishStatus.published}
        )
        return doc is not None


class NewsPublicationRepository(BaseRepository[NewsPublicationRecord]):
    def __init__(
        self, collection_name: str = NEWS_PUBLICATIONS_COLLECTION,
        model: type[NewsPublicationRecord] = NewsPublicationRecord,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)

    async def mark_published(self, record: NewsPublicationSchema, search_field: str = 'gid') -> None:
        await super().mark_published(record, search_field=search_field)

    async def mark_failed(self, record: NewsPublicationSchema, error: str, search_field: str = 'gid') -> None:
        await super().mark_failed(record, error, search_field=search_field)

    async def was_published(self, gid: str, channel: str = "telegram") -> bool:
        doc = await self._collection.find_one(
            {"gid": gid, "channel": channel, "status": PublishStatus.published}
        )
        return doc is not None


class RedditPostPublicationRepository(BaseRepository[RedditPostPublication]):
    def __init__(
        self, collection_name: str = REDDIT_PUBLICATIONS_COLLECTION,
        model: type[RedditPostPublication] = RedditPostPublication,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)

    async def mark_published(self, record: RedditPostPublicationSchema, search_field: str = 'reddit_id') -> None:
        await super().mark_published(record, search_field=search_field)

    async def mark_failed(self, record: RedditPostPublicationSchema, error: str, search_field: str = 'reddit_id') -> None:
        await super().mark_failed(record, error, search_field=search_field)

    async def was_published(
        self, reddit_post: RankedRedditPost | RedditPostPublicationSchema, channel: str = "telegram"
    ) -> bool:
        query = {
            '$or': [
                {"reddit_id": reddit_post.reddit_id},
                {"title": reddit_post.title, "author": reddit_post.author}
        ],
             "channel": channel, "status": PublishStatus.published
        }
        doc = await self._collection.find_one(query)

        return doc is not None


class DiscountPublicationRepository(BaseRepository[DiscountPublication]):

    def __init__(
        self, collection_name: str = DISCOUNT_PUBLICATIONS_COLLECTION,
        model: type[DiscountPublication] = DiscountPublication,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)

    async def mark_published(self, record: DiscountPublicationSchema, search_field="steam_appid") -> None:
        await super().mark_published(record, search_field=search_field)

    async def mark_failed(self, record: DiscountPublicationSchema, error: str, search_field="steam_appid") -> None:
        await super().mark_failed(record, error, search_field=search_field)

    async def was_published(self, discount: DiscountPublicationSchema, channel: str = "telegram") -> bool:
        now = datetime.now()
        doc = await self._collection.find_one(
            {
                "steam_appid": discount.steam_appid, "channel": channel, "status": PublishStatus.published,
                "updated_at": {"$gte": now - timedelta(days=C.DISCOUNT_PUBLICATION_DAYS_LIMIT)},
                "new_price": {"$gte": discount.new_price}
            }
        )
        return doc is not None


class CheckedEntityRepository(BaseRepository[CheckedEntity]):
    def __init__(
        self, collection_name: str = CHECKED_ENTITIES_COLLECTION,
        model: type[CheckedEntity] = CheckedEntity,
        db: AsyncIOMotorDatabase | None = None
    ) -> None:
        super().__init__(collection_name, model, db)
