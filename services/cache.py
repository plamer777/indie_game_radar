from __future__ import annotations
import json
from typing import Optional, Any
import asyncio
from redis.asyncio import from_url
from config.settings import settings


class RedisCache:
    def __init__(self, redis_url: str = settings.REDIS_URL) -> None:
        self._redis = from_url(redis_url, decode_responses=True)
        self._lock = asyncio.Lock()

    async def get_json(self, key: str) -> Optional[dict[str, Any]]:
        raw = await self._redis.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    async def set_json(self, key: str, value: dict[str, Any], ttl: int) -> None:
        data = json.dumps(value, ensure_ascii=False)
        await self._redis.set(key, data, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)
