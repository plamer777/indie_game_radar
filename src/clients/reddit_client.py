from typing import List, Optional, Literal, AsyncGenerator
from asyncpraw import Reddit
from asyncpraw.models import Submission
from src.config.settings import settings
from src.utils.logging import get_logger
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
        """Creates the Reddit object only when it is actually needed."""
        if self._reddit is None:
            self._reddit = Reddit(
                client_id=self._client_id,
                client_secret=self._client_secret,
                user_agent=self._user_agent,
            )
        return self._reddit

    async def find_submissions(
        self,
        query: str,
        subreddit_list: Optional[List[str]] = None,
        sort: Literal['new', 'hot', 'rising', 'controversial', 'top', 'gilded'] = 'new',
        limit: int | None = None,
    ) -> AsyncGenerator[Submission, None]:
        """
        Searches for posts related to a game by name and/or Steam AppID.
        Can be restricted to a list of subreddits.
        """
        log = self._log.bind(query=query)
        log.info("search reddit posts")
        self._ensure_client()

        # if subreddits are specified — join them with +
        subreddits = "all"
        if subreddit_list:
            subreddits = "+".join(subreddit_list)
        subreddit_obj = await self._reddit.subreddit(subreddits)

        async for submission in subreddit_obj.search(query, sort=sort, limit=limit):
            yield submission

    async def close(self):
        if self._reddit:
            await self._reddit.close()
            self._reddit = None
