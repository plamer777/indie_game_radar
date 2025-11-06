from __future__ import annotations
import httpx
import asyncio
from typing import Any, Optional
from src.clients.base import BaseAPIClient
from src.config.constants import TOO_MANY_REQUESTS_DELAY
from src.exceptions.api_exceptions import TooManyRequestsException
from src.schemas.igdb_schemas import IGDBMetaSchema
from src.utils.common import repeat_execution_async
from src.clients.shared_dependencies.rate_limiter import SemaphoreLimiter
from src.managers.cache import RedisCache
from src.utils.logging import get_logger
from src.config.settings import settings
from src.models import PopularityMetrics
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class AsyncIGDBClient(BaseAPIClient):
    def __init__(
        self, cache: RedisCache, client_id: str = settings.IGDB_CLIENT_ID,
        client_secret: str = settings.IGDB_CLIENT_SECRET,
        base_url: str = settings.IGDB_BASE_URL,
        oauth_url: str = settings.TWITCH_OAUTH_URL,
    ) -> None:
        super().__init__()
        self._client = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)
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

    @repeat_execution_async(attempts=5, excepts=(TooManyRequestsException,), delay=TOO_MANY_REQUESTS_DELAY)
    async def _ensure_token(self) -> str:
        if self._access_token:
            return self._access_token
        resp = await self._client.post(
            settings.TWITCH_OAUTH_URL,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "client_credentials",
            },
        )
        if resp.status_code == httpx.codes.TOO_MANY_REQUESTS:
            self._delay += 0.1
            raise TooManyRequestsException("Too many requests")

        resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token")

        self._access_token = token
        return token

    async def _get_headers(self) -> dict:
        token = await self._ensure_token()
        return {
            "Client-ID": self._client_id,
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/plain"
        }

    @repeat_execution_async(attempts=5, excepts=(TooManyRequestsException,), delay=TOO_MANY_REQUESTS_DELAY)
    async def _igdb_post(self, endpoint: str, query: str) -> list[dict[str, Any]] | None:
        url = f"{settings.IGDB_BASE_URL}/{endpoint}"
        headers = await self._get_headers()

        async with self._limiter:
            await asyncio.sleep(self._delay)
            res = await self._client.post(url, content=query, headers=headers)
            if res.status_code == httpx.codes.UNAUTHORIZED:
                # token expired, refresh once
                self._access_token = None
                _ = await self._ensure_token()
                headers["Authorization"] = f"Bearer {self._access_token}"
                res = await self._client.post(url, content=query, headers=headers)
            elif res.status_code == httpx.codes.TOO_MANY_REQUESTS:
                self._delay += 0.1
                raise TooManyRequestsException("Too many requests")
            elif res.status_code in [httpx.codes.BAD_REQUEST, httpx.codes.NOT_FOUND]:
                return None

            res.raise_for_status()
            return res.json()

    async def fetch_game_meta(
        self, *, name: Optional[str] = None, igdb_id: Optional[int] = None, steam_appid: Optional[int] = None
    ) -> Optional[IGDBMetaSchema]:
        """The method fetches game meta from IGDB API by name, igdb_id or steam_appid
        :param name: Game name
        :param igdb_id: IGDB game ID
        :param steam_appid: Steam app ID
        :return: IGDBMetaSchema object or None
        """
        if not name and not igdb_id and not steam_appid:
            return None

        params = {'name': name, 'igdb_id': igdb_id, 'steam_appid': steam_appid}
        game = await self._fetch_meta_by_params(params)
        if not game:
            return None

        # Popularity metrics from separate endpoints (if needed). For now basic metrics
        metrics = await self.fetch_popularity_metrics(game.get('id'))
        meta = IGDBMetaSchema(
            igdb_id=game["id"],
            name=game.get("name", ""),
            summary=game.get("summary"),
            storyline=game.get("storyline"),
            genres=[g.get("name") for g in (game.get("genres") or []) if g and g.get("name")],
            platforms=[p.get("name") for p in (game.get("platforms") or []) if p and p.get("name")],
            release_date=game.get("first_release_date"),
            cover_url=(game.get("cover") or {}).get("url"),
            screenshots=[],
            websites=[w.get("url") for w in (game.get("websites") or []) if w and w.get("url")],
            themes=[t.get("name") for t in (game.get("themes") or []) if t and t.get("name")],
            keywords=[k.get("name") for k in (game.get("keywords") or []) if k and k.get("name")],
            videos=[v.get("video_id") for v in (game.get("videos") or []) if v and v.get("video_id")],
            artworks=[a.get("url") for a in (game.get("artworks") or []) if a and a.get("url")],
            game_engines=[e.get("name") for e in (game.get("game_engines") or []) if e and e.get("name")],
            metrics=metrics,
        )

        return meta

    async def _fetch_meta_by_params(self, params: dict[str, Optional[int]]) -> Optional[dict]:
        for key, value in params.items():
            if not value:
                continue
            value = str(value)
            if key == 'igdb_id':
                query = (
                    f"fields id,name,summary,storyline,genres.name,platforms.name,first_release_date,cover.url,"
                    f"websites.url,themes.name,keywords.name,videos.video_id,artworks.url,game_engines.name; "
                    f"where id = {value};"
                )
            elif key == 'steam_appid':
                query = (
                    f"fields id,name,summary,storyline,genres.name,platforms.name,first_release_date,cover.url,"
                    f"websites.url,external.steam,themes.name,keywords.name,videos.video_id,artworks.url,"
                    f"game_engines.name; where external.steam = {value};"
                )
            else:
                safe_name = value.replace('"', '\\"') if value else ""
                query = (
                    "search \"" + safe_name + "\"; "
                    f"fields id,name,summary,storyline,genres.name,platforms.name,first_release_date,cover.url,"
                    f"websites.url,themes.name,keywords.name,videos.video_id,artworks.url,game_engines.name; "
                    f"limit {C.IGDB_SEARCH_LIMIT};"
                )
            data = await self._igdb_post("games", query)
            if data:
                return data[0]
            return None

    async def fetch_popularity_metrics(self, igdb_id: int) -> PopularityMetrics:

        query = f"""
            fields id, rating, rating_count, aggregated_rating, aggregated_rating_count,
            total_rating, total_rating_count, follows, hypes;
            where id = {igdb_id};
        """
        data = await self._igdb_post("games", query)
        metrics = PopularityMetrics()
        if data:
            g = data[0]
            metrics = PopularityMetrics(
                follows=g.get("follows", C.ZERO) or C.ZERO,
                hypes=g.get("hypes", C.ZERO) or C.ZERO,
                rating=g.get("rating"),
                rating_count=g.get("rating_count", C.ZERO) or C.ZERO,
                aggregated_rating=g.get("aggregated_rating"),
                aggregated_rating_count=g.get("aggregated_rating_count", C.ZERO) or C.ZERO,
                total_rating=g.get("total_rating"),
                total_rating_count=g.get("total_rating_count", C.ZERO) or C.ZERO,
                popularity=None,
            )

        return metrics
