from datetime import datetime, UTC

from src.clients.telegram_client import TelegramPublisher
from src.db.repositories import (
    GamePublicationRepository, DiscountPublicationRepository, NewsPublicationRepository,
    RedditPostPublicationRepository
)
from src.models.publication import PublishStatus, ReviewSummary
from src.schemas import AllocatedPostsSchema
from src.services.base_service import BaseService
from src.services.publisher_service.editors import EditorialRefiner
from src.services.publisher_service.renderers.tg_post_renderer import PostRenderer
from src.utils.common import clean_text
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class PublisherService(BaseService):

    def __init__(
        self, publication_repo: GamePublicationRepository, publisher: TelegramPublisher,
        discount_publication_repo: DiscountPublicationRepository,
        news_publication_repo: NewsPublicationRepository,
        reddit_post_publication_repo: RedditPostPublicationRepository,
        editorial_refiner: EditorialRefiner
    ):
        self._game_publication_repo = publication_repo
        self._discount_publication_repo = discount_publication_repo
        self._news_publication_repo = news_publication_repo
        self._reddit_post_publication_repo = reddit_post_publication_repo
        self._publisher = publisher
        self._log = get_logger().bind(service="PublisherService")
        self._renderer = PostRenderer()
        self._editor = editorial_refiner
        self._repo_mapper = {
            "games": self._game_publication_repo,
            "discounts": self._discount_publication_repo,
            "news": self._news_publication_repo,
            "reddit_posts": self._reddit_post_publication_repo,
            "reddit_memes": self._reddit_post_publication_repo,
        }

    async def count_published_for_today(self) -> int:
        """Подсчитывает количество опубликованных постов за сегодня"""
        start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        end = datetime.now(UTC).replace(hour=23, minute=59, second=59, microsecond=999999)
        params = {
            "status": PublishStatus.published,
            "created_at": {
                "$gte": start,
                "$lte": end,
            },
        }
        published_games = await self._game_publication_repo.get_all(params)
        published_discounts = await self._discount_publication_repo.get_all(params)
        published_news = await self._news_publication_repo.get_all(params)
        published_posts = await self._reddit_post_publication_repo.get_all(params)
        return len(published_games) + len(published_discounts) + len(published_news) + len(published_posts)

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
            if record.category == 'news':
                params = {
                    "title": record.post.title,
                    "content": clean_text(record.post.contents),
                }
                edited = await self._editor.refine(record.category, **params)
                record.post.title = edited.get('title')
                record.post.contents = edited.get('content')
            elif record.category == 'reddit_posts':
                params = {
                    "title": record.post.title,
                    "content": clean_text(record.post.selftext),
                }
                post_type = f'{record.category}_{record.post.type}'
                edited = await self._editor.refine(post_type, **params)
                record.post.title = edited.get('title')
                record.post.selftext = edited.get('content')
            elif record.category == 'games':
                params = {
                    "title": record.post.name,
                    "content": clean_text(record.post.detailed_description),
                }
                edited = await self._editor.refine(record.category, **params)
                record.post.detailed_description = edited.get('content')
            elif record.category == 'reviews':
                params = {
                    "game": record.post.game_name,
                    "reviews": [review.model_dump() for review in record.post.reviews or []],
                }
                edited = await self._editor.refine(record.category, **params)
                record.post.summary = ReviewSummary(**edited)

            text = self._renderer.render(record)
            if not publication_repo:
                raise ValueError(f"Unsupported publication type: {record.category}")

            if record.category == 'reddit_memes':
                photo = record.post.url or record.post.preview_images[0]
                msg_id = await self._publisher.publish_photo(photo, text, schedule_time=record.publish_time)
            else:
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
