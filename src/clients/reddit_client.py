from datetime import datetime
from typing import List, Optional, Literal
from asyncpraw import Reddit
from asyncpraw.models import Submission
from src.config.settings import settings
from src.schemas import RedditPostSchema
from src.utils.logging import get_logger
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class RedditClient:
    def __init__(
        self,
        client_id: str = settings.REDDIT_CLIENT_ID,
        client_secret: str = settings.REDDIT_CLIENT_SECRET,
        user_agent: str = settings.REDDIT_USER_AGENT,
    ) -> None:
        self._reddit: Reddit | None = None
        self._client_id = client_id
        self._client_secret = client_secret
        self._user_agent = user_agent
        self._log = get_logger().bind(client="reddit")

    def _ensure_client(self) -> Reddit:
        """Создает Reddit объект только когда это действительно нужно."""
        if self._reddit is None:
            self._reddit = Reddit(
                client_id=self._client_id,
                client_secret=self._client_secret,
                user_agent=self._user_agent,
            )
        return self._reddit

    async def fetch_meta_indie_posts(
        self, queries: list[str] = C.INDIE_DEV_QUERIES, limit: int = C.DEFAULT_GAME_DEV_STORY_POSTS_LIMIT,
        subreddit_list: Optional[List[str]] = C.GAMEDEV_SUBREDDITS,
    )  -> list[RedditPostSchema]:
        query = " OR ".join(queries)

        subreddits = "+".join(subreddit_list)
        self._ensure_client()
        subreddit_obj = await self._reddit.subreddit(subreddits)

        posts = []
        async for submission in subreddit_obj.search(query, sort="new", limit=limit):
            post_model = await self._map_submission(submission, post_type='game_dev_story')
            posts.extend(post_model)

        return posts

    async def search_posts_for_game(
        self,
        steam_appid: int,
        subreddit_list: Optional[List[str]] = C.GAMEDEV_SUBREDDITS,
        limit: int = C.DEFAULT_GAME_RELATED_POSTS_LIMIT
    ) -> List[RedditPostSchema]:
        """
        Ищет посты, связанные с игрой: по названию и/или по Steam AppID.
        Можно ограничить списком сабреддитов.
        """
        log = self._log.bind(appid=steam_appid)
        log.info("search_posts_for_game")
        self._ensure_client()
        results: List[RedditPostSchema] = []
        query = f'"store.steampowered.com/app/{steam_appid}"'

        # если указаны сабреддиты — объединяем через +
        subreddits = "all"
        if subreddit_list:
            subreddits = "+".join(subreddit_list)
        subreddit_obj = await self._reddit.subreddit(subreddits)

        async for submission in subreddit_obj.search(query, sort="new", limit=limit):
            try:
                post_model = await self._map_submission(submission, steam_appid)
                results.append(post_model)
            except Exception as e:
                log.warning(f"Failed to map submission {submission.id}: {e}")
        return results

    async def _map_submission(
        self,
        submission: Submission,
        steam_appid: Optional[int] = None,
        post_type: Literal['game_related', 'game_dev_story'] = 'game_related'
    ) -> RedditPostSchema:
        # извлечение steam_appid из URL или текста, если не передан
        extracted_appid: Optional[int] = steam_appid
        match = C.REDDIT_STEAM_URL_RE.search(submission.url or "")
        if match:
            try:
                extracted_appid = int(match.group(1))
            except ValueError:
                pass

        # snippet: берем первые ~150 символов selftext
        snippet = None
        if submission.selftext:
            snippet = submission.selftext.strip().replace("\n", " ")[:150]

        # preview images
        preview_images = None
        if hasattr(submission, "preview") and submission.preview:
            try:
                preview_images = [img["source"]["url"] for img in submission.preview["images"]]
            except Exception:
                preview_images = None

        # media urls
        media_urls = None
        if submission.media and hasattr(submission.media, "items"):
            try:
                media_urls = [v for v in submission.media.values() if type(v) is str]
            except Exception:
                media_urls = None

        # get subreddit subscribers if available
        try:
            subreddit_subs = await submission.subreddit.subscribers
        except Exception:
            subreddit_subs = None

        edited_utc = None
        if submission.edited and isinstance(submission.edited, (int, float)):
            edited_utc = datetime.fromtimestamp(submission.edited)

        model = RedditPostSchema(
            reddit_id=submission.id,
            fullname=submission.name,
            type=post_type,
            steam_appid=extracted_appid,
            title=submission.title,
            selftext=submission.selftext or None,
            selftext_html=getattr(submission, "selftext_html", None),
            url=submission.url,
            permalink=f"https://reddit.com{submission.permalink}",
            domain=submission.domain,
            author=getattr(submission.author, "name", None),
            author_fullname=getattr(submission.author, "fullname", None) if submission.author else None,
            author_is_blocked=getattr(submission.author, "is_blocked", None) if submission.author else None,
            author_premium=getattr(submission.author, "is_gold", None) if submission.author else None,
            subreddit=submission.subreddit.display_name,
            subreddit_id=submission.subreddit_id,
            subreddit_name_prefixed=submission.subreddit_name_prefixed,
            subreddit_type=submission.subreddit_type,
            subreddit_subscribers=subreddit_subs,
            created_utc=datetime.fromtimestamp(submission.created_utc),
            edited_utc=edited_utc,
            score=submission.score,
            ups=getattr(submission, "ups", None),
            downs=getattr(submission, "downs", None),
            upvote_ratio=getattr(submission, "upvote_ratio", None),
            num_comments=submission.num_comments,
            num_crossposts=getattr(submission, "num_crossposts", None),
            over_18=submission.over_18,
            is_self=submission.is_self,
            is_video=submission.is_video,
            is_original_content=getattr(submission, "is_original_content", None),
            thumbnail=submission.thumbnail if submission.thumbnail != "self" else None,
            thumbnail_height=getattr(submission, "thumbnail_height", None),
            thumbnail_width=getattr(submission, "thumbnail_width", None),
            preview_images=preview_images,
            media_urls=media_urls,
            total_awards_received=getattr(submission, "total_awards_received", None),
            all_awardings=getattr(submission, "all_awardings", None),
            post_hint=getattr(submission, "post_hint", None),
            link_flair_text=getattr(submission, "link_flair_text", None),
            link_flair_template_id=getattr(submission, "link_flair_template_id", None),
            extract_snippet=snippet,
            crawl_time=datetime.now(),
        )
        return model

    async def close(self):
        if self._reddit:
            await self._reddit.close()
            self._reddit = None
