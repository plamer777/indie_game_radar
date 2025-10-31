from src.clients.telegram_client import TelegramPublisher
from src.db.repositories import (
    GamePublicationRepository, DiscountPublicationRepository, NewsPublicationRepository,
    RedditPostPublicationRepository
)
from src.models.publication import PublishStatus
from src.schemas import AllocatedPostsSchema
from src.services.base_service import BaseService
from src.services.publisher_service.renderers.tg_post_renderer import PostRenderer
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class PublisherService(BaseService):

    def __init__(
        self, publication_repo: GamePublicationRepository, publisher: TelegramPublisher,
        discount_publication_repo: DiscountPublicationRepository,
        news_publication_repo: NewsPublicationRepository,
        reddit_post_publication_repo: RedditPostPublicationRepository,
    ):
        self._game_publication_repo = publication_repo
        self._discount_publication_repo = discount_publication_repo
        self._news_publication_repo = news_publication_repo
        self._reddit_post_publication_repo = reddit_post_publication_repo
        self._publisher = publisher
        self._log = get_logger().bind(service="PublisherService")
        self._renderer = PostRenderer()
        self._repo_mapper = {
            "games": self._game_publication_repo,
            "discounts": self._discount_publication_repo,
            "news": self._news_publication_repo,
            "reddit_posts": self._reddit_post_publication_repo,
        }

    async def schedule_publications(self, posts: list[AllocatedPostsSchema]):
        """Публикует (или планирует) посты в соответствии с их временем"""
        cycle_log = self._log.bind(service="schedule_publications")
        cycle_log.info("start")
        published_count = 0
        for record in posts:
            published = await self._handle_publication(record)
            if not published.post.error:
                published_count += 1

        cycle_log.info("cycle_end", published=published_count)

    async def _handle_publication(self, record: AllocatedPostsSchema):
        """Планирует или сразу публикует пост"""
        publication_repo = self._repo_mapper.get(record.category)
        try:
            text = self._renderer.render(record)
            if not publication_repo:
                raise ValueError(f"Unsupported publication type: {record.category}")
            msg_id = await self._publisher.publish_message(text, schedule_time=record.publish_time)
            if msg_id:
                record.post.message_id = msg_id
                record.post.status = PublishStatus.published
                await publication_repo.mark_published(record.post)
                self._log.info("publish_success", category=record.category, msg_id=msg_id)
                return record
            else:
                raise Exception("Telegram returned no message_id")
        except Exception as e:
            record.post.status = PublishStatus.failed
            record.post.error = str(e)
            await publication_repo.mark_failed(record.post, error=str(e))
            self._log.error("publish_failed", category=record.category, error=str(e))
            return record
