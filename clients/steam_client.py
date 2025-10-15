from __future__ import annotations
import httpx
import asyncio
from typing import Any, Optional, AsyncGenerator
import numpy as np
from schemas import GameSchema
from schemas.game_schemas import AppSchema
from utils.retry import RetryPolicy
from services.rate_limiter import SemaphoreLimiter
from services.cache import RedisCache
from utils.logging import get_logger
from config.settings import settings
from models.game import CurrentPlayersResponse, AchievementStatsResponse, \
    AchievementPct, ReviewResponse, ReviewAuthor, ReviewItem, SteamExtendedInfo, PriceInfo, NewsStats
from datetime import datetime, UTC
from config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class AsyncSteamClient:
    def __init__(
        self, cache: RedisCache, api_key: str = settings.STEAM_API_KEY,
        web_api_base_url: str = settings.STEAM_WEBAPI_BASE,
        store_base_url: str = settings.STEAM_STORE_BASE
    ) -> None:
        self._client = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)
        self._retry = RetryPolicy(
            retries=settings.HTTP_MAX_RETRIES,
            base_delay=settings.HTTP_RETRY_BACKOFF_BASE,
            max_delay=settings.HTTP_RETRY_BACKOFF_MAX,
            retry_exceptions=(httpx.HTTPError, asyncio.TimeoutError),
        )
        self._limiter = SemaphoreLimiter(settings.STEAM_MAX_CONCURRENCY)
        self._cache = cache
        self._log = get_logger().bind(client="steam")
        self._api_key = api_key
        self._base_web_api_url = web_api_base_url
        self._base_store_api_url = store_base_url
        self._format = 'json'

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_apps(
        self, batch_size: int | None = None, since: int | datetime | None = None
    ) -> AsyncGenerator[list[AppSchema], None]:
        url = f"{self._base_web_api_url}/IStoreService/GetAppList/v1/"
        params = {'key': self._api_key, 'format': self._format}
        if since:
            params['if_modified_since'] = since if isinstance(since, int) else int(since.timestamp())
        params.update({'max_results': batch_size} if batch_size else {})
        async with self._limiter:
            async def _do():
                res = await self._client.get(url, params=params)
                res.raise_for_status()
                data = res.json()
                result = data.get("response", {})
                return result
            while True:
                result = await self._retry.run(_do)
                have_more = result.get('have_more_results')
                apps = result.get('apps', [])
                last_app_id = result.get('last_appid')
                params['last_appid'] = last_app_id
                yield [AppSchema(**app) for app in apps]
                if not have_more:
                    break

    async def fetch_app_news(
        self, app_id: int, count: int = C.NEWS_COUNT, max_length: int | None = None
    ) -> dict:
        url = f"{self._base_web_api_url}/ISteamNews/GetNewsForApp/v0002/"
        params = {'key': self._api_key, 'format': self._format, 'appid': app_id, 'count': count}
        if max_length:
            params['maxlength'] = max_length
        async with self._limiter:
            async def _do():
                res = await self._client.get(url, params=params)
                if res.status_code in [403, 404]:
                    return None
                res.raise_for_status()
                data = res.json()
                return data.get('appnews', {}).get("newsitems", [])

            return await self._retry.run(_do)

    def compute_news_stats(self, timestamps: list[int]) -> NewsStats:
        """Агрегирует статистику по новостям для игры."""

        if not timestamps:
            return NewsStats(
                total_news_last_30d=0,
                total_news_last_90d=0,
                days_since_last_news=None,
                avg_interval_days=None,
            )

        now = datetime.now(UTC).timestamp()
        last_news_ts = max(timestamps)
        days_since_last = (now - last_news_ts) / C.SECONDS_IN_DAY

        sorted_ts = sorted(timestamps)
        intervals = (
            np.diff(sorted_ts) / C.SECONDS_IN_DAY if len(sorted_ts) > 1 else []
        )

        total_30d = sum(now - t < C.NEWS_WINDOW_30D * C.SECONDS_IN_DAY for t in timestamps)
        total_90d = sum(now - t < C.NEWS_WINDOW_90D * C.SECONDS_IN_DAY for t in timestamps)

        return NewsStats(
            total_news_last_30d=total_30d,
            total_news_last_90d=total_90d,
            days_since_last_news=round(days_since_last, C.ROUND_PRECISION),
            avg_interval_days=(
                round(np.mean(intervals), C.ROUND_PRECISION) if len(intervals) else None
            ),
        )

    async def fetch_full_info(self, appid: int) -> GameSchema | None:
        game = await self.fetch_app_details(appid)
        if not game:
            return None
        # параллельно запрашиваем дополнительные
        current_players = await self.fetch_current_players(appid)
        achievements = await self.fetch_achievements(appid)
        reviews = await self.fetch_reviews(appid)
        news = await self.fetch_app_news(appid)

        # объединяем в модель (если ты расширишь GameModel или добавишь поле ext_info)
        game.ext_info = SteamExtendedInfo(
            steam_appid=appid,
            current_players=current_players.player_count if current_players else None,
            achievements=achievements,
            review_summary=reviews,
            news_stats=self.compute_news_stats([n.get("date") for n in news]),
        )
        return game

    async def fetch_app_details(self, appid: int) -> Optional[GameSchema]:
        url = f"{self._base_store_api_url}/api/appdetails"
        params = {'key': self._api_key, 'format': self._format, 'appids': appid, 'l': 'en', 'cc': 'us'}
        async with self._limiter:
            async def _do():
                res = await self._client.get(url, params=params)
                if res.status_code in [403, 404]:
                    return None
                res.raise_for_status()
                payload = res.json()
                raw = payload.get(str(appid))
                if not raw or not raw.get("success"):
                    return None
                return self._normalize_game(appid, raw.get("data", {}))
            game = await self._retry.run(_do)

        return game

    def _normalize_game(self, appid: int, data: dict[str, Any]) -> Optional[GameSchema]:
        name = data.get("name")
        if not name:
            return None
        release_date = None
        try:
            if data.get("release_date", {}).get("coming_soon"):
                raise ValueError('the game is not released yet')
            rd = data.get("release_date", {}).get("date")
            if rd:
                release_date = datetime.strptime(rd, "%b %d, %Y") if "," in rd else datetime.strptime(rd, "%b %Y")
        except Exception:
            release_date = None

        price_info = None
        price_overview = data.get("price_overview") or {}
        if price_overview:
            try:
                price_info = PriceInfo(
                    currency=price_overview.get("currency", "USD"),
                    initial=(price_overview.get("initial", C.ZERO) / C.STEAM_PRICE_DIVISOR),
                    final=(price_overview.get("final", C.ZERO) / C.STEAM_PRICE_DIVISOR),
                    discount_percent=price_overview.get("discount_percent", C.ZERO),
                )
            except Exception:
                price_info = None

        try:
            gm = GameSchema(
                steam_appid=appid,
                name=name,
                short_description=data.get("short_description"),
                detailed_description=data.get("detailed_description"),
                supported_languages=data.get("supported_languages"),
                release_date=release_date,
                genres=data.get("genres", []),
                categories=[c.get("description") for c in data.get("categories", []) if c.get("description")],
                developers=data.get("developers", []),
                publishers=data.get("publishers", []),
                website=data.get("website"),
                header_image=data.get("header_image"),
                background=data.get("background") or data.get("background_raw"),
                screenshots=data.get("screenshots", []),
                price=price_info,
                is_free=bool(data.get("is_free")),
                recommendations=data.get("recommendations"),
                platforms=data.get("platforms"),
                package_groups=data.get("package_groups", []),
            )

            return gm

        except Exception:
            self._log.warning("normalize_failed", appid=appid)
            return None

    async def fetch_current_players(self, appid: int) -> Optional[CurrentPlayersResponse]:
        url = f"{self._base_web_api_url}/ISteamUserStats/GetNumberOfCurrentPlayers/v1"
        params = {'key': self._api_key, 'appid': appid, 'format': self._format}
        async with self._limiter:
            async def _do():
                resp = await self._client.get(url, params=params)
                if resp.status_code in [403, 404]:
                    return None
                resp.raise_for_status()
                j = resp.json().get("response", {})
                if "player_count" in j:
                    return CurrentPlayersResponse(player_count=j["player_count"])
                return None

            return await self._retry.run(_do)

    async def fetch_achievements(self, appid: int) -> Optional[AchievementStatsResponse]:
        url = f"{self._base_web_api_url}/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/"
        params = {'gameid': appid, 'format': self._format}
        async with self._limiter:
            async def _do():
                resp = await self._client.get(url, params=params)
                if resp.status_code in [403, 404]:
                    return None
                resp.raise_for_status()
                j = resp.json().get("achievementpercentages", {})
                ach_list = j.get("achievements", [])
                return AchievementStatsResponse(
                    achievements=[
                        AchievementPct(name=a["name"], percent=a["percent"])
                        for a in ach_list
                        if "name" in a and "percent" in a
                    ]
                )

            return await self._retry.run(_do)

    async def fetch_reviews(
        self, appid: int, cursor: Optional[str] = None, num_per_page: int = 20
    ) -> Optional[ReviewResponse]:
        # This is Store Reviews API (not part of WebAPI), use store_base_url
        url = f"{self._base_store_api_url}/appreviews/{appid}"
        params = {
            'json': 1,
            'language': 'all',
            'num_per_page': num_per_page,
            'day_range': C.REVIEW_DAY_RANGE
        }
        if cursor:
            params['cursor'] = cursor

        async with self._limiter:
            async def _do():
                resp = await self._client.get(url, params=params)
                if resp.status_code in [403, 404]:
                    return None
                resp.raise_for_status()
                j = resp.json()
                reviews = []
                for r in j.get("reviews", []):
                    # map fields
                    author = ReviewAuthor(
                        steamid=r.get("author", {}).get("steamid"),
                        num_games_owned=r.get("author", {}).get("num_games_owned"),
                        num_reviews=r.get("author", {}).get("num_reviews"),
                        played_for=r.get("author", {}).get("playtime_forever"),
                    )
                    reviews.append(
                        ReviewItem(
                            author=author,
                            review=r.get("review"),
                            language=r.get("language"),
                            timestamp_created=r.get("timestamp_created"),
                            voted_up=r.get("voted_up"),
                            votes_up=r.get("votes_up"),
                            votes_funny=r.get("votes_funny"),
                        )
                    )
                review_summary = j.get("query_summary", {})
                ratio = review_summary.get("total_positive") / review_summary.get("total_reviews")
                return ReviewResponse(
                    total_reviews=review_summary.get("total_reviews"),
                    total_negative=review_summary.get("total_negative"),
                    total_positive=review_summary.get("total_positive"),
                    ratio = round(ratio, 3),
                    review_score=review_summary.get("review_score"),
                    reviews=reviews,
                    cursor=j.get("cursor")
                )

            return await self._retry.run(_do)
