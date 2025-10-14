from __future__ import annotations
import httpx
import asyncio
from typing import Any, Optional

from schemas.igdb_schemas import IGDBMetaSchema, PopularityMetricsSchema
from utils.retry import RetryPolicy
from services.rate_limiter import SemaphoreLimiter
from services.cache import RedisCache
from utils.logging import get_logger
from config.settings import settings
from models.igdb import PopularityMetrics
from datetime import datetime, UTC
from config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class AsyncIGDBClient:
    def __init__(
        self, cache: RedisCache, client_id: str = settings.IGDB_CLIENT_ID,
        client_secret: str = settings.IGDB_CLIENT_SECRET,
        base_url: str = settings.IGDB_BASE_URL,
        oauth_url: str = settings.TWITCH_OAUTH_URL,
    ) -> None:
        self._client = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)
        self._retry = RetryPolicy(
            retries=settings.HTTP_MAX_RETRIES,
            base_delay=settings.HTTP_RETRY_BACKOFF_BASE,
            max_delay=settings.HTTP_RETRY_BACKOFF_MAX,
            retry_exceptions=(httpx.HTTPError, asyncio.TimeoutError),
        )
        self._limiter = SemaphoreLimiter(settings.IGDB_MAX_CONCURRENCY)
        self._cache = cache
        self._log = get_logger().bind(client="igdb")
        self._access_token: Optional[str] = None
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url
        self._oauth_url = oauth_url

    async def close(self) -> None:
        await self._client.aclose()

    async def _ensure_token(self) -> str:
        if self._access_token:
            return self._access_token

        async def _do():
            resp = await self._client.post(
                settings.TWITCH_OAUTH_URL,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "grant_type": "client_credentials",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("access_token")

        token = await self._retry.run(_do)
        self._access_token = token
        return token

    async def _get_headers(self) -> dict:
        token = await self._ensure_token()
        return {
            "Client-ID": self._client_id,
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/plain"
        }

    async def _igdb_post(self, endpoint: str, query: str) -> list[dict[str, Any]]:
        url = f"{settings.IGDB_BASE_URL}/{endpoint}"
        headers = await self._get_headers()

        async with self._limiter:
            async def _do():
                res = await self._client.post(url, content=query, headers=headers)
                if res.status_code == httpx.codes.UNAUTHORIZED:
                    # token expired, refresh once
                    self._access_token = None
                    _ = await self._ensure_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    res = await self._client.post(url, content=query, headers=headers)
                res.raise_for_status()
                return res.json()
            return await self._retry.run(_do)

    async def fetch_game_meta(
        self, *, name: Optional[str] = None, igdb_id: Optional[int] = None
    ) -> Optional[IGDBMetaSchema]:
        if not name and not igdb_id:
            return None

        if igdb_id:
            query = (
                f"fields id,name,summary,storyline,genres.name,platforms.name,first_release_date,cover.url,"
                f"websites.url; where id = {igdb_id};"
            )
        else:
            safe_name = name.replace('"', '\\"') if name else ""
            query = (
                "search \"" + safe_name + "\"; "
                f"fields id,name,summary,storyline,genres.name,platforms.name,first_release_date,cover.url,"
                f"websites.url; limit {C.IGDB_SEARCH_LIMIT};"
            )
        data = await self._igdb_post("games", query)
        if not data:
            return None
        game = data[0]

        # Popularity metrics from separate endpoints (if needed). For now basic metrics
        metrics = await self.fetch_popularity_metrics(igdb_id)
        meta = IGDBMetaSchema(
            igdb_id=game["id"],
            name=game.get("name", ""),
            summary=game.get("summary"),
            storyline=game.get("storyline"),
            genres=[g.get("name") for g in (game.get("genres") or []) if g and g.get("name")],
            platforms=[p.get("name") for p in (game.get("platforms") or []) if p and p.get("name")],
            release_date=datetime.fromtimestamp(game["first_release_date"], UTC) if game.get("first_release_date") else None,
            cover_url=(game.get("cover") or {}).get("url"),
            screenshots=[],
            websites=[w.get("url") for w in (game.get("websites") or []) if w and w.get("url")],
            metrics=metrics,
        )
        await self._cache.set_json(cache_key, meta.model_dump(), ttl=settings.CACHE_TTL_IGDB_META)
        return meta

    async def fetch_popularity_metrics(self, igdb_id: int) -> PopularityMetricsSchema:

        query = f"fields follows,hypes,rating,rating_count,aggregated_rating,aggregated_rating_count; where id = {igdb_id};"
        data = await self._igdb_post("games", query)
        metrics = PopularityMetrics()
        if data:
            g = data[0]
            metrics = PopularityMetricsSchema(
                follows=g.get("follows", C.ZERO) or C.ZERO,
                hypes=g.get("hypes", C.ZERO) or C.ZERO,
                rating=g.get("rating"),
                rating_count=g.get("rating_count", C.ZERO) or C.ZERO,
                aggregated_rating=g.get("aggregated_rating"),
                aggregated_rating_count=g.get("aggregated_rating_count", C.ZERO) or C.ZERO,
                popularity=None,
            )

        return metrics
