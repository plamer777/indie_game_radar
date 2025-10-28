"""This file contains a BaseRepo class with base MongoDB CRUD methods"""
import asyncio
import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime, timezone
from typing import Generic, TypeVar, AsyncGenerator
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, TypeAdapter
from src.db.mongo import get_database
from src.config.constants import STATIC_FIELDS, IGNORED_FIELDS
# -------------------------------------------------------------------------
UTC = timezone.utc
M = TypeVar('M', bound=BaseModel)
# -------------------------------------------------------------------------


class AbstractRepository(ABC):
    """The AbstractRepository class with interface for MongoDB CRUD methods"""
    @abstractmethod
    def __init__(self, collection: str, model, db) -> None:
        pass

    @abstractmethod
    def add_new(self, data: dict) -> dict:
        pass

    @abstractmethod
    def get_all(self, params) -> list[dict]:
        pass

    @abstractmethod
    def get_by_id(self, uid: str) -> dict:
        pass

    @abstractmethod
    def delete(self, uid: str) -> None:
        pass


class BaseRepository(AbstractRepository, Generic[M]):
    """The BaseRepo class with base MongoDB CRUD methods"""
    def __init__(
        self, collection: str, model: type[M] | None = None, db: AsyncIOMotorDatabase | None = None
    ) -> None:
        """Initializes the BaseRepo class
        :param collection: a str representing the name of the MongoDB
        collection
        :param model: a Pydantic model class
        """
        db = db or get_database()
        logging.info(f'Db: {db}')
        self._collection = db[collection]
        self._model = model
        self._adapter = TypeAdapter(model) if model else None

    async def add_new(self, data: dict) -> M | dict:
        """This method adds a new record to the database
        :param data: a dict representing the data to add
        :return: a Pydantic instance
        """
        model = await self._collection.insert_one(data)
        new_record = await self.get_by_id(model.inserted_id)
        return (self._model.model_validate(new_record)
                if self._model else new_record)

    async def add_list_new(self, data: list[dict]):
        """This method adds a list of new records to the database
        :param data: a list of dict representing the data to add
        """
        if data:
            await self._collection.insert_many(data)

    async def add_or_update(
        self, data: list[dict | BaseModel] | dict | BaseModel, search_field: str = 'id',
        ignore_fields: list[str] = IGNORED_FIELDS, static_fields: list[str] = STATIC_FIELDS,
        fields_to_remove: list[str] = None, update_all: bool = False, ignore_errors: bool = False
    ) -> set[str]:
        """This method adds or updates a records in the database
        :param data: a dict representing the data to add or update
        :param search_field: a str representing the field to search record by
        :param ignore_fields: a list of str representing the fields to ignore
        while checking for equality of existing and new records
        :param static_fields: a list of str representing the fields that
        should not be updated
        :param update_all: a bool representing whether to update all existing
        records or not while checking for equality of existing and new ones
        :param fields_to_remove: a list of str representing the fields to
        remove from the new record
        :param ignore_errors: a bool representing whether to ignore errors during add or update process
        """
        tasks = []
        ignore_fields = ignore_fields or []
        static_fields = static_fields or []
        fields_to_remove = fields_to_remove or []
        changed = set()
        # игнорируем статичные поля при сравнении тоже
        fields_ignored_for_comparison = set(ignore_fields) | set(static_fields)
        data = data if isinstance(data, list) else [data]

        if data and isinstance(data[0], BaseModel):
            data = [record.model_dump() for record in data]

        for record in data:
            record = deepcopy(record)
            try:
                # удалить явно заданные поля
                [record.pop(key, None) for key in fields_to_remove]

                # нормализовать значение поля поиска
                search_value = record.get(search_field)
                if search_field == '_id' and search_value is not None and not isinstance(search_value, ObjectId):
                    try:
                        search_value = ObjectId(search_value)
                        record[search_field] = search_value
                    except Exception:
                        # если невалидный ObjectId — оставляем как есть
                        pass

                if search_field != '_id' and search_value in (None, ''):
                    logging.warning(f'Search field value not found: {search_field}, skipping record')
                    continue

                found = await self._collection.find_one({search_field: search_value})
                if found:
                    # подготовка для сравнения (без _id)
                    existing_clean = deepcopy(found)
                    existing_clean.pop('_id', None)

                    new_clean = deepcopy(record)
                    new_clean.pop('_id', None)

                    # посчитать изменения с учётом игноров и статичных полей
                    changes = self._calc_changes(existing_clean, new_clean, fields_ignored_for_comparison)

                    if update_all or changes:
                        # статичные поля не апдейтим даже если отличаются
                        update_doc = {k: v for k, v in changes.items() if k not in static_fields}
                        if update_doc:
                            update_doc.update(
                                {
                                    key: record.get(key) for key in ignore_fields
                                    if record.get(key) and key not in static_fields
                                }
                            )

                            tasks.append(
                                self._collection.update_one({search_field: search_value}, {'$set': update_doc})
                            )
                            changed.add(search_value)
                        else:
                            # отличия только в статичных/игнорируемых полях — пропускаем
                            continue
                else:
                    # новая запись — вставка как есть
                    tasks.append(self._collection.insert_one(record))
                    changed.add(record.get(search_field))

            except Exception as e:
                logging.error(f'Cannot prepare record to add or update: {e}')
                if not ignore_errors:
                    raise e

        for completed_task in asyncio.as_completed(tasks):
            try:
                 await completed_task
            except Exception as e:
                logging.error(f'Cannot add or update record: {e}')
                if not ignore_errors:
                    raise e

        return changed

    @staticmethod
    def _calc_changes(existing_record: dict, new_record: dict, ignored_fields: set[str] | list[str]) -> dict:
        """Return fields from new_record that differ from existing_record excluding ignored_fields.
        Missing keys are treated as differences. Shallow comparison.
        :param existing_record: a dict representing the existing record
        :param new_record: a dict representing the new record
        :param ignored_fields: a list of str representing the fields to ignore
        :return: a dict representing the changes
        """
        ignored = set(ignored_fields or [])
        keys = (set(existing_record.keys()) | set(new_record.keys())) - ignored
        changes: dict = {}
        for k in keys:
            if existing_record.get(k) != new_record.get(k):
                changes[k] = new_record.get(k)
        return changes

    async def get_all(
        self, params: dict | None = None, limit: int = 0, skip: int = 0,
        show_deleted: bool = False, sort_by: dict | None = None, generator_mode: bool = False
    ) -> list[M | dict] | AsyncGenerator[M | dict, None]:
        """This method returns all records from the database
        :param limit: an int representing the number of records to return
        :param skip: an int representing the number of records to skip
        :param params: a dict representing the query parameters
        :param show_deleted: a boolean representing whether to show deleted
        records or not
        :param sort_by: a dict representing the sort order
        :param generator_mode: a boolean representing whether to return a generator or a list of records
        :return: a list of Pydantic instances
        """
        result = []
        if not params:
            params = {}
        if not show_deleted:
            params.update({'deleted_at': None})

        found = self._collection.find(params).limit(limit or 0).skip(skip or 0)
        if sort_by:
            found = found.sort(list(sort_by.items()))
        if not generator_mode:
            if self._model:
                result = [
                    self._model.model_validate(item) async for item in found]
            else:
                async for item in found:
                    item['_id'] = str(item['_id'])
                    result.append(item)

            return result
        else:
            return self._get_all_generator(params, limit, skip, show_deleted, sort_by)

    async def _get_all_generator(
        self, params: dict | None = None, limit: int = 0, skip: int = 0, show_deleted: bool = False,
        sort_by: dict | None = None
    ) -> AsyncGenerator[M | dict, None]:
        """This method returns all records from the database
        :param limit: an int representing the number of records to return
        :param skip: an int representing the number of records to skip
        :param params: a dict representing the query parameters
        :param show_deleted: a boolean representing whether to show deleted
        records or not
        :param sort_by: a dict representing the sort order
        :return: a list of Pydantic instances
        """
        if not params:
            params = {}
        if not show_deleted:
            params.update({'deleted_at': None})

        found = self._collection.find(params).limit(limit or 0).skip(skip or 0)
        if sort_by:
            found = found.sort(list(sort_by.items())).allow_disk_use(True)
        if self._model:
            async for item in found:
                yield self._model.model_validate(item)
        else:
            async for item in found:
                item['_id'] = str(item['_id'])
                yield item

    async def get_by_id(self, uid: str, show_deleted: bool = False) -> M | dict | None:
        """This method returns a single record from the database
        :param uid: a str representing the id of the record
        :param show_deleted: a boolean representing whether to show deleted records or not
        :return: a Pydantic instance
        """
        try:
            uid = ObjectId(uid)
        except Exception as e:
            pass
        params = {'_id': uid}
        if not show_deleted:
            params.update({'deleted_at': None})
        found = await self._collection.find_one(params)
        if found:
            return self._model.model_validate(found) if self._model else found

    async def get_one(self, params: dict, show_deleted: bool = False) -> M | dict | None:
        """This method returns a single record from the database
        :param params: a dict representing the query parameters to find the
        record
        :param show_deleted: a boolean representing whether to show deleted
        records or not
        :return: a Pydantic instance
        """
        if not show_deleted:
            params.update({'deleted_at': None})
        found = await self._collection.find_one(params)
        if found:
            return self._model.model_validate(found) if self._model else found

        return {}

    async def update(
        self, uid: str | dict, data: dict, id_field: str = '_id', many: bool = False
    ) -> bool:
        """This method updates a record in the database
        :param uid: a str representing the id of the record to update
        :param data: a dict representing the data to update
        :param id_field: a str representing the field to search record by (default: '_id')
        :param many: a boolean representing whether to update multiple records
        :return: a bool representing the result of the update
        """
        if not data:
            return False

        if id_field == '_id' and type(uid) is not dict:
            try:
                uid = ObjectId(uid)
            except Exception as e:
                pass
        try:
            update_method = self._collection.update_one if not many else self._collection.update_many
            updated = await update_method({id_field: uid} if type(uid) is not dict else uid, {'$set': data})
            if updated:
                return True
        except Exception as e:
            logging.error(f'Cannot update record: {e}')
        return False

    async def delete(self, uid: str | int | dict, many: bool = False, delete_permanently: bool = False) -> None:
        """This method deletes a record from the database
        :param uid: a str representing the id of the record to delete. You could
        provide it as a string or ObjectID value if you'd like to use default
        _id pk or as a dict like: {'source_id' : '123'} to use another field
        :param many: a boolean representing whether to delete multiple records
        or not
        :param delete_permanently: a boolean representing whether to delete the record or records from the database
        permanently without the soft delete feature
        """
        try:
            found = await self.get_by_id(uid) if type(uid) is str else await self.get_one(uid)
            if not found:
                raise ValueError(f'Record {uid} Not found')
            elif found.get('deleted_at') if type(found) is dict else found.deleted_at:
                raise ValueError('Record already deleted')

            update_method = self._collection.update_one if not many else self._collection.update_many
            delete_method = self._collection.delete_one if not many else self._collection.delete_many
            if type(uid) is str:
                try:
                    uid = ObjectId(uid)
                except Exception as e:
                    pass
            if not delete_permanently:
                current_date = datetime.now()
                await update_method(
                    {'_id': uid} if not many and type(uid) in (str, ObjectId) else uid,
                    {'$set': {'deleted_at': current_date, 'updated_at': current_date}})
            else:
                await delete_method(
                    {'_id': uid} if not many and type(uid) in (str, ObjectId) else uid)
        except Exception as e:
            logging.error(f'Cannot delete record: {e}')

    async def delete_duplicated(self, search_parameter: str, date_field: str, soft_delete: bool = True) -> dict:
        """
        The method serves to find records by provided field with duplicated values of the field and delete all excessive
        ones sorted by provided date field, all records with duplicated values and older values of date field will be
        deleted
        Args:

        Returns:
            list: Список _id документов, которые нужно удалить.
        """
        try:
            pipeline = [
                {
                '$match': {
                    "deleted_at": None
                    }
                },
                {
                    "$group": {
                        "_id": "$" + search_parameter,  # Группируем по параметру поиска
                        "docs": {"$push": "$$ROOT"},  # Собираем все документы в массив
                        "count": {"$sum": 1}  # Считаем количество документов
                    }
                },
                {
                    "$match": {"count": {"$gt": 1}}  # Оставляем только группы с более чем одним документом
                },
                {
                    "$unwind": "$docs"  # Разворачиваем массив документов для сортировки
                },
                {
                    "$sort": {f"docs.{date_field}": 1}  # Сортируем документы внутри каждой группы
                },
                {
                    "$group": {
                        "_id": "$_id",  # Сохраняем _id (значение параметра поиска)
                        "ids_to_delete": {"$push": "$docs._id"},  # собираем _id всех документов в массив
                        "docs": {"$push": "$docs"}
                    }
                },
                {
                    "$project": {
                        "_id": 0,  # Нам не нужен _id группы
                        "ids_to_delete": {  # Нам нужен новый массив _id для удаления
                            "$slice": ["$ids_to_delete", 0, {"$subtract": [{"$size": "$ids_to_delete"}, 1]}]
                        }
                    }
                },
                {
                    "$unwind": "$ids_to_delete"
                },
                {
                    "$group": {
                        "_id": None,
                        "ids_to_delete": {"$push": "$ids_to_delete"}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "ids_to_delete": 1
                    }
                }
            ]

            result = self._collection.aggregate(pipeline)
            result = [item async for item in result]
            if result and result[0] and "ids_to_delete" in result[0]:
                ids_to_delete = result[0]["ids_to_delete"]
            else:
                ids_to_delete = []

            await self.delete({'_id': {'$in': ids_to_delete}}, many=True, delete_permanently=not soft_delete)
            return {'deleted': len(ids_to_delete)}

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            return {'deleted': 0}

    async def get_unique_fields(self, field_name: str) -> list[str]:
        """This method returns a list of unique values of provided field
        :param field_name: a str representing the name of the field
        :return: a list of unique values
        """
        found = await self._collection.distinct(field_name)
        return found

    async def get_max_value(
        self, field_name: str = 'updated_at',
        params: dict | None = None
    ) -> dict[str, str]:
        """This method is used to get the max field value from the
        database by the provided field name
        :param field_name: a string representing the name of the document field
        to retrieve a max value from
        :param params: a dict representing the parameters to filter MongoDB
        aggregated result
        :return: a string representing the max value of the provided field"""

        params = params or {}

        result = self._collection.aggregate(
            [
                {'$match': params},
                {'$group': {
                    '_id': 'max_value', 'max_value': {'$max': f'${field_name}'}
                }}
            ],
            allowDiskUse=True
        )

        try:
            max_value = await anext(result)
        except Exception:
            max_value = {}

        return max_value
