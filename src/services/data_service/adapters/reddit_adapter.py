from datetime import datetime
from typing import Literal, Optional
from asyncpraw.models import Submission
from src.clients import RedditClient
from src.schemas import RedditPostSchema
from src.utils.logging import get_logger
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class RedditAdapter:
    def __init__(self, client: RedditClient):
        self._client = client
        self._log = get_logger().bind(adapter="RedditAdapter")

    async def fetch_game_pixel_art(
        self,
        game_names: list[str],
        subreddit_list: Optional[list[str]] = ["PixelArt"],
        limit: int = C.DEFAULT_GAME_MEME_POSTS_LIMIT,
        oversample_factor: int = 20,
    ) -> list[RedditPostSchema]:
        """
        Загружает Pixel Art, если в заголовке поста упоминается одна из игр списка.
        """
        log = self._log
        log.info(f"fetch_game_pixel_art for {len(game_names)} games")

        posts = []
        fetched = 0
        target = limit

        # Нам нужно загрузить НАМНОГО больше постов, чтобы найти среди них те,
        # которые относятся к нашим играм.
        internal_limit = limit * oversample_factor

        game_names_lower = [name.lower().strip() for name in game_names if len(name.strip()) > 2]

        query = ' OR '.join(f'title:"{name}"' for name in game_names_lower)

        if not query:
            return []

        # Убираем поиск по flair, так как в r/PixelArt флеры другие (например "Hand Pixelled")
        # Просто берем 'hot' или 'top'
        async for submission in self._client.find_submissions(
            query=query,
            subreddit_list=subreddit_list, sort="hot", limit=internal_limit
        ):
            log.info(submission.title)
            # 1. Фильтр: Только изображения
            if not submission.url or not submission.url.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                continue

            # 2. Фильтр: Проверка на NSFW (для артов это критично)
            if submission.over_18:
                continue

            # 3. Фильтр: Поиск названия игры в заголовке
            title_lower = submission.title.lower()

            # Проверяем, содержится ли хоть одно название игры в заголовке
            # Используем 'in', чтобы найти 'Hades' внутри 'Fanart of Zagreus from Hades!'
            is_relevant = any(game in title_lower for game in game_names_lower)

            if not is_relevant:
                continue

            try:
                # Передаем post_type="art", чтобы потом правильно оформить пост (например, добавить хештег #PixelArt)
                post_model = await self._map_submission(submission, post_type="art")
            except Exception as e:
                log.warning(f"Ошибка при маппинге поста: {e}")
                continue

            posts.append(post_model)
            fetched += 1

            if fetched >= target:
                break

        log.info(f"Found {fetched} pixel art posts out of scanned submissions")
        return posts

    async def fetch_gaming_memes(
        self,
        subreddit_list: Optional[list[str]] = C.GAME_MEME_SUBREDDITS,
        limit: int = C.DEFAULT_GAME_MEME_POSTS_LIMIT,
        oversample_factor: int = C.GAME_MEME_OVERSAMPLE_FACTOR,
    ) -> list[RedditPostSchema]:
        """
        Загружает свежие игровые мемы.
        oversample_factor — во сколько раз увеличить лимит исходной выборки,
        чтобы компенсировать отсеивание нерелевантных постов.
        """
        log = self._log
        log.info("fetch_gaming_memes")
        posts = []
        fetched = 0
        target = limit

        # внутренний лимит больше внешнего, чтобы компенсировать отсеивание
        internal_limit = limit * oversample_factor

        async for submission in self._client.find_submissions(
                "flair:Meme", sort="hot", limit=internal_limit, subreddit_list=subreddit_list
        ):
            # фильтруем только изображения
            if not submission.url or not submission.url.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                continue

            try:
                post_model = await self._map_submission(submission, post_type="meme")
            except Exception as e:
                log.warning(f"Ошибка при маппинге поста: {e}")
                continue

            posts.append(post_model)
            fetched += 1

            if fetched >= target:
                break  # достигли нужного количества отфильтрованных постов

        return posts

    async def search_posts_for_game(
        self,
        steam_appid: int,
        subreddit_list: Optional[list[str]] = C.GAMEDEV_SUBREDDITS,
        limit: int = C.DEFAULT_GAME_RELATED_POSTS_LIMIT
    ) -> list[RedditPostSchema]:
        """
        Ищет посты, связанные с игрой: по названию и/или по Steam AppID.
        Можно ограничить списком сабреддитов.
        """
        log = self._log.bind(appid=steam_appid)
        log.info("search_posts_for_game")
        results: list[RedditPostSchema] = []
        query = f'"store.steampowered.com/app/{steam_appid}"'
        async for submission in self._client.find_submissions(query, subreddit_list, limit=limit):
            try:
                post_model = await self._map_submission(submission, steam_appid)
                results.append(post_model)
            except Exception as e:
                log.warning(f"Failed to map submission {submission.id}: {e}")
        return results

    async def fetch_meta_indie_posts(
        self,
        queries: list[str] = C.GAMEDEV_DISCUSSION_QUERIES,
        limit: int = C.DEFAULT_GAME_DEV_STORY_POSTS_LIMIT,
        subreddit_list: Optional[list[str]] = C.GAMEDEV_SUBREDDITS,
    ) -> list[RedditPostSchema]:
        log = self._log.bind(queries=queries)
        log.info("fetch_meta_indie_posts")
        posts = []
        for q in queries:
            try:
                async for submission in self._client.find_submissions(
                    q, sort="hot", limit=limit // len(queries), subreddit_list=subreddit_list
                ):
                    post_model = await self._map_submission(submission, post_type="game_dev_story")
                    posts.append(post_model)
            except Exception as e:
                log.error(f"⚠️ Query '{q}' failed: {e}")

        # убираем дубликаты по id
        unique_posts = {p.id: p for p in posts}.values()
        return list(unique_posts)

    async def _map_submission(
        self,
        submission: Submission,
        steam_appid: Optional[int] = None,
        post_type: Literal['game_related', 'game_dev_story', 'meme', 'art'] = 'game_related'
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