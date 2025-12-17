# src/clients/direct_reddit_sdk.py
import asyncio
import random
import time
from typing import Optional, AsyncGenerator, Literal, Iterable, Dict
import httpx
from rapidfuzz import fuzz
from src.clients.models.reddit_client_models import Author, Subreddit, Submission
from src.config import constants as C
from src.config.constants import SECONDS_IN_DAY
# ---------------------------------------------------------------------------------------------------------------------


class DirectRedditClient:
    """
    Advanced direct Reddit JSON client (no official OAuth).
    - Uses reddit.com/r/<subreddit>/.json endpoints
    - Persistent httpx.AsyncClient with optional UA rotation and proxy support
    - Smart search: fuzzy/title/url/appid/slug matching
    """

    def __init__(
        self,
        base_url: str = C.DIRECT_REDDIT_CLIENT_BASE_URL,
        ua_pool: Optional[Iterable[str]] = None,
        rotate_ua: bool = False,
        proxies: Optional[Dict[str, str]] = None,
        fuzz_threshold: int = C.DIRECT_REDDIT_CLIENT_FUZZ_THRESHOLD
    ):
        self._base_url = base_url.rstrip("/")
        self._rotate_ua = rotate_ua
        self._ua_pool = list(ua_pool or C.DIRECT_REDDIT_CLIENT_DEFAULT_UA_POOL)
        self._fuzz_threshold = fuzz_threshold
        self._cache = {}
        self._loop = asyncio.get_event_loop()
      
        self._client = httpx.AsyncClient(
            http2=True,
            headers=C.DIRECT_REDDIT_CLIENT_DEFAULT_HEADERS,
            timeout=C.DIRECT_REDDIT_CLIENT_TIMEOUT,
            proxy=proxies
        )
        # small lock to avoid overlapping requests if caller is aggressive
        self._lock = asyncio.Lock()

    def _build_headers(self) -> dict:
        h = dict(C.DIRECT_REDDIT_CLIENT_DEFAULT_HEADERS)
        if self._rotate_ua and self._ua_pool:
            h["User-Agent"] = random.choice(self._ua_pool)
        return h

    def _get_cache_data(self, key: str) -> Optional[dict]:
        """The method serves to retrieve cache data by provided key
        :param key: a string representing the key to retrieve data for
        """
        return self._cache.get(key)

    def _set_cache_data(self, key: str, data: dict | list) -> None:
        """The method serves to set cache data by provided key
        :param key: a string representing the key to set data for
        :param data: a dictionary representing the data to set
        """
        self._cache[key] = data

    async def _sleep_jitter(self):
        await asyncio.sleep(random.uniform(C.DIRECT_REDDIT_CLIENT_MIN_DELAY, C.DIRECT_REDDIT_CLIENT_MAX_DELAY))

    async def _get_json(self, path: str, params: dict | None = None) -> Optional[dict]:
        """The method sends a GET request to the specified path with optional parameters and returns the JSON response.
        
        Args:
            path (str): The path to send the GET request to.
            params (dict | None, optional): Optional parameters to include in the request. Defaults to None.
        
        Returns:
            Optional[dict]: The JSON response from the request, or None if the request fails.
        """
        key = f"{path}?{params}" if params else path
        cache_data = self._get_cache_data(key)
        if cache_data:
            return cache_data

        url = f"{self._base_url.rstrip('/')}/{path.lstrip('/')}"
        last_err = None
        for attempt in range(1, C.DIRECT_REDDIT_CLIENT_MAX_RETRIES + 1):
            try:
                # small lock to serialize requests if needed
                async with self._lock:
                    headers = self._build_headers()
                    resp = await self._client.get(url, params=params, headers=headers)
                # polite jitter after request
                await self._sleep_jitter()

                if resp.status_code == 200:
                    self._set_cache_data(key, resp.json())
                    return resp.json()
                # handle 429/403/500 gracefully with backoff
                if resp.status_code in (429, 502, 503, 504, 403):
                    last_err = (resp.status_code, resp.text[:200])
                    # exponential backoff
                    await asyncio.sleep(min(5 * attempt, 30))
                    continue
                # for other statuses log and break
                last_err = (resp.status_code, resp.text[:200])
                break
            except httpx.RequestError as e:
                last_err = e
                await asyncio.sleep(min(0.5 * attempt, 5))
                continue
        # final failure
        # you can replace prints with proper logging
        print("DirectRedditSDK: _get_json failed:", last_err)
        return None

    async def close(self) -> None:
        """The method serves to close client"""
        await self._client.aclose()

    def clean_cache(self) -> None:
        """The method serves to clean cache"""
        self._cache.clear()

    @staticmethod
    def _slugify(s: str) -> str:
        """The method converts a string to a slug by removing non-alphanumeric characters and converting to lowercase.
        
        Args:
            s (str): The string to convert to a slug.
        
        Returns:
            str: The slugified string.
        """
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", s.lower())
        return slug.strip("-")

    async def find_submissions(
        self,
        subreddit_list: list[str],
        limit: int = 50,
        query: Optional[str] = None,
        sort: Literal["hot", "new", "top", "rising"] = "hot",
        max_age_days: Optional[int] = 7
    ) -> AsyncGenerator[Submission, None]:
        """
        Yields reddit items (raw data dict from reddit .json 'data.children[].data').
        - subreddit: single subreddit name (we iterate per-subreddit at caller level)
        - limit: desired number of posts to return (per subreddit)
        - query: optional string for fuzzy/title matching (if provided)
        - sort: reddit sort param
        - max_age_days: if provided, ignore posts older than this
        
        Returns:
            AsyncGenerator[Submission, None]: An async generator yielding Submission objects.
        """
        per_request = 100  # maximum Reddit page size
        returned = 0
        after = None
        max_age_ts = None
        if max_age_days is not None:
            max_age_ts = time.time() - max_age_days * SECONDS_IN_DAY

        # if query looks like a steam url or contains appid, optionally convert
        query_slug = None
        if query:
            query_slug = self._slugify(query)

        while returned < limit:
            for subreddit in subreddit_list:

                params = {"limit": min(per_request, limit - returned)}
                if sort:
                    params["sort"] = sort
                if after:
                    params["after"] = after

                path = f"r/{subreddit}/.json"
                data = await self._get_json(path, params=params)
                if not data or "data" not in data:
                    break

                children = data["data"].get("children", [])
                if not children:
                    break

                # update cursor
                after = data["data"].get("after")
                if not after:
                    # no more pages
                    pass

                for child in children:
                    d = child.get("data", {})
                    # skip older posts
                    if max_age_ts and d.get("created_utc", 0) < max_age_ts:
                        continue
                        
                    # fuzzy/title filtering
                    if query:
                        title = (d.get("title") or "")
                        selftext = (d.get("selftext") or "")
                        score_title = fuzz.partial_ratio(query, title)
                        score_text = fuzz.partial_ratio(query, selftext)
                        score_slug = 0
                        if query_slug and d.get("url"):
                            score_slug = 100 if query_slug in (d.get("url") or "").lower() else 0
                        best = max(score_title, score_text, score_slug)
                        if best < self._fuzz_threshold:
                            continue
                    # yield result
                    yield self._convert_item(d)
                    returned += 1
                    if returned >= limit:
                        break

                # if no cursor, break
                if not after:
                    break
                    
    def _convert_item(self, d: dict) -> Submission:
        """The method converts a raw Reddit submission dictionary to a Submission object.
        
        Args:
            d (dict): A dictionary containing the raw Reddit submission data.
        
        Returns:
            Submission: A Submission object representing the converted data.
        """
        author = Author(
            name=d.get("author"),
            fullname=d.get("author_fullname"),
            is_blocked=d.get("author_is_blocked", False),
            is_gold=d.get("author_premium", False),
        )

        subreddit = Subreddit(
            display_name=d["subreddit"],
            subscribers=d.get("subreddit_subscribers"),
            id=d.get("subreddit_id"),
            name_prefixed=d.get("subreddit_name_prefixed", f"r/{d['subreddit']}"),
            type=d.get("subreddit_type", "public"),
        )

        return Submission(
            id=d["id"],
            name=d.get("name", "t3_" + d["id"]),
            title=d["title"],
            selftext=d.get("selftext"),
            selftext_html=d.get("selftext_html"),
            url=d.get("url"),
            permalink=d.get("permalink", ""),
            domain=d.get("domain", ""),
            author=author,
            subreddit=subreddit,
            subreddit_id=d.get("subreddit_id"),
            subreddit_name_prefixed=d.get("subreddit_name_prefixed", f"r/{d['subreddit']}"),
            subreddit_type=d.get("subreddit_type", "public"),
            created_utc=d.get("created_utc", 0),
            edited=d.get("edited"),
            score=d.get("score", 0),
            ups=d.get("ups", 0),
            downs=d.get("downs", 0),
            upvote_ratio=d.get("upvote_ratio"),
            num_comments=d.get("num_comments", 0),
            num_crossposts=d.get("num_crossposts"),
            over_18=d.get("over_18", False),
            is_self=d.get("is_self", False),
            is_video=d.get("is_video", False),
            is_original_content=d.get("is_original_content"),
            thumbnail=d.get("thumbnail"),
            thumbnail_height=d.get("thumbnail_height"),
            thumbnail_width=d.get("thumbnail_width"),
            preview=d.get("preview"),
            media=d.get("media"),
        )
    