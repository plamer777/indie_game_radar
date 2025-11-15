import random
from jinja2 import Environment, BaseLoader, select_autoescape
from src.schemas import (
    GamePublicationRecordSchema,
    DiscountPublicationSchema,
    NewsPublicationSchema,
    RedditPostPublicationSchema,
    AllocatedPostsSchema,
)
from src.templates import (
    GAME_POST_TEMPLATES,
    DISCOUNT_POST_TEMPLATES,
    NEWS_POST_TEMPLATES,
    REDDIT_POST_TEMPLATES,
)
from src.templates.reddit_meme_puplications import REDDIT_MEME_TEMPLATES
from src.utils.common import clean_text
# ---------------------------------------------------------------------------------------------------------------------


class PostRenderer:
    """Universal Telegram post renderer using Jinja2"""

    def __init__(self) -> None:
        """The constructor for the PostRenderer class."""
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=select_autoescape(enabled_extensions=('html', 'xml')),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self._builders = {
            "games": self._render_game_post,
            "discounts": self._render_discount_post,
            "news": self._render_news_post,
            "reddit_posts": self._render_reddit_post,
            "reddit_memes": self._render_meme_post,
        }

    # ------------------------------------------------------------
    def render(self, record: AllocatedPostsSchema) -> str:
        """Selects and renders post template by category"""
        record_type = record.category.lower()
        if record_type not in self._builders:
            raise ValueError(f"Unsupported publication type: {record_type}")
        return self._builders[record_type](record.post)

    # ------------------------------------------------------------
    # --- GAME POST ---
    def _render_game_post(self, game: GamePublicationRecordSchema) -> str:
        """Renders a game post template.
        :param game: The game to render
        :return: The rendered game post template
        """
        context = {
            "name": game.name,
            "short_description": game.detailed_description or game.short_description or "",
            "developers": ', '.join(game.developers or []) if game.developers else "-",
            "publishers": ', '.join(game.publishers or []) if game.publishers else "-",
            "genres": ', '.join(game.genres or []) if game.genres else "unique style",
            "platforms": ', '.join([p for p, v in game.platforms.model_dump().items() if v]) if game.platforms else "—",
            "supported_languages": clean_text(game.supported_languages) or "—",
            "release_date": game.release_date.strftime("%B %d, %Y") if game.release_date else "—",
            "website": game.website,
            "steam_appid": game.steam_appid,
            "tags": ', '.join(game.tags or []) if game.tags else None,
            "image_url": getattr(game, "header_image", None),
            "recommendations": game.recommendations or '-',
            "price": f'{game.price.final}$' if game.price else 'Free' if game.is_free else '-',
        }

        template = self.env.from_string(random.choice(GAME_POST_TEMPLATES))
        return template.render(**context).strip()

    # ------------------------------------------------------------
    # --- DISCOUNT POST ---
    def _render_discount_post(self, disc: DiscountPublicationSchema) -> str:
        """Renders a discount post template.
        :param disc: The discount to render
        :return: The rendered discount post template
        """
        context = {
            "name": disc.name,
            "original_price": disc.old_price,
            "price": disc.new_price,
            "discount_percent": int(disc.percent_drop),
            "short_description": disc.detailed_description or disc.short_description or "",
            "genres": ', '.join(disc.genres or []) if disc.genres else "unique style",
            "steam_appid": disc.steam_appid,
            "tags": ', '.join(disc.tags or []) if disc.tags else None,
            "image_url": getattr(disc, "header_image", None),
        }

        template = self.env.from_string(random.choice(DISCOUNT_POST_TEMPLATES))
        return template.render(**context).strip()

    # ------------------------------------------------------------
    # --- NEWS POST ---
    def _render_news_post(self, news: NewsPublicationSchema) -> str:
        """Renders a news post template.
        :param news: The news to render
        :return: The rendered news post template
        """
        context = {
            "title": news.title,
            "contents": news.contents or "",
            "appid": news.appid,
            "feedlabel": news.feedlabel or "Steam News",
            "author": news.author or "—",
            "date": news.date.strftime("%B %d, %Y") if news.date else "—",
            "url": news.url,
            "image_url": getattr(news, "header_image", None),
            "steam_appid": getattr(news, "appid", None),
        }

        template = self.env.from_string(random.choice(NEWS_POST_TEMPLATES))
        return template.render(**context).strip()

    # ------------------------------------------------------------
    # --- REDDIT POST ---
    def _render_reddit_post(self, post: RedditPostPublicationSchema) -> str:
        """Renders a Reddit post template.
        :param post: The Reddit post to render
        :return: The rendered Reddit post template
        """
        context = {
            "title": post.title,
            "selftext": post.selftext or "",
            "author": post.author or "Unknown",
            "subreddit": post.subreddit or "unknown",
            "score": post.ups or 0,
            "num_comments": post.num_comments or 0,
            "ups": post.ups or 0,
            "permalink": post.permalink or "",
            "image_url": post.preview_images[0] if post.preview_images else None,
            "steam_appid": getattr(post, "steam_appid", None),
        }

        template = self.env.from_string(random.choice(REDDIT_POST_TEMPLATES))
        return template.render(**context).strip()

    def _render_meme_post(self, post: RedditPostPublicationSchema) -> str:
        """Renders a meme post template.
        :param post: The meme post to render
        :return: The rendered meme post template
        """
        context = {
            "title": post.title,
            "subreddit": post.subreddit or "unknown"
        }

        template = self.env.from_string(random.choice(REDDIT_MEME_TEMPLATES))
        return template.render(**context).strip()
