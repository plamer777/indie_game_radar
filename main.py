from __future__ import annotations
import asyncio
from src.clients import RedditClient

from src.container import orchestrator
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


async def app_main() -> None:
    log = get_logger().bind(app="igr")
    log.info("app_start")
    # client = RedditClient()
    # posts = await client.fetch_meta_indie_posts()
    # print(posts)
    # posts = await client.search_posts_for_game(
    #     "Dying Light", steam_appid=239140,
    #     limit=30,
    #     subreddit_list=["IndieDev", "GameDev", "DevLogs", "IndieGameDev"]
    #     # subreddit_list=['IndieGame', 'IndieGames', 'IndieGameDev', 'Indie', 'IndieGaming']
    # )
    # print(posts)

    await orchestrator.start()

    log.info("app_stop")


if __name__ == "__main__":
    asyncio.run(app_main())
