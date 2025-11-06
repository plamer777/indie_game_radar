from __future__ import annotations
import httpx
import asyncio
from typing import Any, Optional, AsyncGenerator
from src.clients.base import BaseAPIClient
from src.config.constants import TOO_MANY_REQUESTS_DELAY
from src.exceptions.api_exceptions import TooManyRequestsException, NotFoundException
from src.schemas import GameSchema
from src.schemas.game_schemas import AppSchema
from src.utils.common import repeat_execution_async
from src.clients.shared_dependencies.rate_limiter import SemaphoreLimiter
from src.managers.cache import RedisCache
from src.utils.logging import get_logger
from src.config.settings import settings
from src.models.game import CurrentPlayersResponse, \
    AchievementPct, ReviewResponse, ReviewAuthor, ReviewItem, SteamExtendedInfo, PriceInfo, SteamNewsItem
from datetime import datetime
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class AsyncSteamClient(BaseAPIClient):
    def __init__(
        self, cache: RedisCache, api_key: str = settings.STEAM_API_KEY,
        web_api_base_url: str = settings.STEAM_WEBAPI_BASE,
        store_base_url: str = settings.STEAM_STORE_BASE
    ) -> None:
        super().__init__()
        self._client = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)
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
            attempts = 3
            while True:
                try:
                    await asyncio.sleep(self._delay)

                    response = await self._get_json_response(
                        url, query_params=params,
                        raise_on_status_code={httpx.codes.TOO_MANY_REQUESTS: TooManyRequestsException}
                    )
                    result = response.get("response", {})
                    have_more = result.get('have_more_results')
                    apps = result.get('apps', [])
                    last_app_id = result.get('last_appid')
                    params['last_appid'] = last_app_id
                    yield [AppSchema(**app) for app in apps]
                    if not have_more:
                        break

                except Exception as e:
                    self._delay += 0.1
                    attempts -= 1
                    if attempts == 0:
                        raise e

    @repeat_execution_async(attempts=5, excepts=(TooManyRequestsException,), delay=TOO_MANY_REQUESTS_DELAY)
    async def fetch_app_news(
        self, app_id: int, count: int = C.NEWS_COUNT, max_length: int | None = None
    ) -> list[SteamNewsItem] | None:
            url = f"{self._base_web_api_url}/ISteamNews/GetNewsForApp/v0002/"
            params = {'key': self._api_key, 'format': self._format, 'appid': app_id, 'count': count}
            if max_length:
                params['maxlength'] = max_length
            async with self._limiter:
                try:
                    await asyncio.sleep(self._delay)
                    response = await self._get_json_response(
                        url, query_params=params,
                        raise_on_status_code={
                            httpx.codes.TOO_MANY_REQUESTS: TooManyRequestsException,
                            httpx.codes.NOT_FOUND: NotFoundException,
                            httpx.codes.BAD_REQUEST: NotFoundException
                        }
                    )
                    raw_news = response.get('appnews', {}).get("newsitems", [])
                    return [SteamNewsItem(**news) for news in raw_news]
                except NotFoundException:
                    return None
                except TooManyRequestsException as e:
                    self._delay += 0.1
                    raise e
                except Exception as e:
                    self._log.error("fetch_app_news_failed", appid=app_id, error=str(e))
                    return None

    async def fetch_full_app_details(self, appid: int) -> GameSchema | None:
        log = self._log.bind(appid=appid)
        log.info("fetch_full_app_details")
        game = await self.fetch_app_details(appid)
        if not game:
            return None
        # параллельно запрашиваем дополнительные
        current_players = await self.fetch_current_players(appid)
        achievements = await self.fetch_achievements(appid)
        reviews = await self.fetch_reviews(appid)
        news = await self.fetch_app_news(appid)

        # объединяем в модель (если ты расширишь GameModel или добавишь поле ext_info)
        game.last_news = news
        game.ext_info = SteamExtendedInfo(
            steam_appid=appid,
            current_players=current_players.player_count if current_players else None,
            achievements=achievements,
            review_summary=reviews,
        )
        return game

    @repeat_execution_async(attempts=5, excepts=(TooManyRequestsException,), delay=TOO_MANY_REQUESTS_DELAY)
    async def fetch_app_details(self, appid: int) -> Optional[GameSchema]:
        url = f"{self._base_store_api_url}/api/appdetails"
        params = {'key': self._api_key, 'format': self._format, 'appids': appid, 'l': 'en', 'cc': 'us'}
        async with self._limiter:
            try:
                await asyncio.sleep(self._delay)
                response = await self._get_json_response(
                    url, query_params=params,
                    raise_on_status_code={
                        httpx.codes.TOO_MANY_REQUESTS: TooManyRequestsException,
                        httpx.codes.NOT_FOUND: NotFoundException,
                        httpx.codes.BAD_REQUEST: NotFoundException
                    }
                )
                raw = response.get(str(appid))
                if not raw or not raw.get("success"):
                    return None
                return self._normalize_game(appid, raw.get("data", {}))
            except NotFoundException:
                return None
            except TooManyRequestsException as e:
                self._delay += 0.1
                raise e
            except Exception as e:
                self._log.error("fetch_app_details_failed", appid=appid, error=str(e))
                return None

    def _normalize_game(self, appid: int, data: dict[str, Any]) -> Optional[GameSchema]:
        name = data.get("name")
        if not name:
            return None
        release_date = None
        try:
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
                is_coming_soon=data.get("release_date", {}).get("coming_soon"),
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

        except Exception as e:
            self._log.warning("normalize_failed", appid=appid, error=str(e))
            return None

    @repeat_execution_async(attempts=5, excepts=(TooManyRequestsException,), delay=TOO_MANY_REQUESTS_DELAY)
    async def fetch_current_players(self, appid: int) -> Optional[CurrentPlayersResponse]:
        try:
            url = f"{self._base_web_api_url}/ISteamUserStats/GetNumberOfCurrentPlayers/v1"
            params = {'key': self._api_key, 'appid': appid, 'format': self._format}
            async with self._limiter:
                await asyncio.sleep(self._delay)
                response = await self._get_json_response(
                    url, query_params=params,
                    raise_on_status_code={
                        httpx.codes.TOO_MANY_REQUESTS: TooManyRequestsException,
                        httpx.codes.NOT_FOUND: NotFoundException,
                        httpx.codes.BAD_REQUEST: NotFoundException
                    }
                )
                j = response.get("response", {})
                if "player_count" in j:
                    return CurrentPlayersResponse(player_count=j["player_count"])
                return None
        except NotFoundException:
            return None
        except TooManyRequestsException as e:
            self._delay += 0.1
            raise e
        except Exception as e:
            self._log.error("fetch_current_players_failed", appid=appid, error=str(e))
            return None

    @repeat_execution_async(attempts=5, excepts=(TooManyRequestsException,), delay=TOO_MANY_REQUESTS_DELAY)
    async def fetch_achievements(self, appid: int) -> Optional[list[AchievementPct]]:
        try:
            url = f"{self._base_web_api_url}/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/"
            params = {'gameid': appid, 'format': self._format}
            async with self._limiter:
                await asyncio.sleep(self._delay)
                response = await self._get_json_response(
                    url, query_params=params,
                    raise_on_status_code={
                        httpx.codes.TOO_MANY_REQUESTS: TooManyRequestsException,
                        httpx.codes.NOT_FOUND: NotFoundException,
                        httpx.codes.BAD_REQUEST: NotFoundException
                    }
                )
                j = response.get("achievementpercentages", {})
                ach_list = j.get("achievements", [])
                return [
                        AchievementPct(name=a["name"], percent=a["percent"])
                        for a in ach_list if "name" in a and "percent" in a
                    ]
        except NotFoundException:
            return None
        except TooManyRequestsException as e:
            self._delay += 0.1
            raise e
        except Exception as e:
            self._log.error("fetch_achievements_failed", appid=appid, error=str(e))
            return None

    @repeat_execution_async(attempts=5, excepts=(TooManyRequestsException,), delay=TOO_MANY_REQUESTS_DELAY)
    async def fetch_reviews(
        self, appid: int, cursor: Optional[str] = None, num_per_page: int = 20
    ) -> Optional[ReviewResponse]:
        # This is Store Reviews API (not part of WebAPI), use store_base_url
        try:
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
                await asyncio.sleep(self._delay)
                response = await self._get_json_response(
                    url, query_params=params,
                    raise_on_status_code={
                        httpx.codes.TOO_MANY_REQUESTS: TooManyRequestsException,
                        httpx.codes.NOT_FOUND: NotFoundException,
                        httpx.codes.BAD_REQUEST: NotFoundException
                    }
                )

                reviews = []
                for r in response.get("reviews", []):
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
                review_summary = response.get("query_summary", {})

                try:
                    ratio = review_summary.get("total_positive") / review_summary.get("total_reviews")
                except Exception:
                    ratio = 0

                return ReviewResponse(
                    total_reviews=review_summary.get("total_reviews"),
                    total_negative=review_summary.get("total_negative"),
                    total_positive=review_summary.get("total_positive"),
                    ratio=round(ratio, 3),
                    review_score=review_summary.get("review_score"),
                    reviews=reviews,
                    cursor=response.get("cursor")
                )

        except NotFoundException:
            return None
        except TooManyRequestsException as e:
            self._delay += 0.1
            raise e

        except Exception as e:
            self._log.error("fetch_reviews_failed", appid=appid, error=str(e))
            return None