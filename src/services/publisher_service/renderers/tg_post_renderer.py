from pydantic import BaseModel
from src.schemas import GamePublicationRecordSchema, DiscountPublicationSchema, NewsPublicationSchema, \
    RedditPostPublicationSchema, AllocatedPostsSchema


# ---------------------------------------------------------------------------------------------------------------------


class PostRenderer:
    """Universal Telegram post renderer for Indie Game Radar"""

    def __init__(self):
        self._builders = {
            "game": self._render_game_post,
            "discount": self._render_discount_post,
            "news": self._render_news_post,
            "reddit_post": self._render_reddit_post,
        }

    def render(self, record: AllocatedPostsSchema) -> str:
        """Select and render the post template based on record type"""
        record_type = record.category.lower()
        if record_type not in self._builders:
            raise ValueError(f"Unsupported publication type: {record_type}")
        return self._builders[record_type](record)

    # --- Templates ---

    def _render_game_post(self, game: GamePublicationRecordSchema) -> str:
        genres = ", ".join(game.genres) if game.genres else "Unknown"
        devs = ", ".join(game.developers) if game.developers else "Unknown"
        tags = ", ".join(game.tags[:5]) if game.tags else ""
        price = (
            "Free to play 🆓"
            if game.is_free
            else f"💰 {game.price.final if game.price else 'N/A'}"
        )
        release = (
            "Coming soon 🚀"
            if game.is_coming_soon
            else f"Released on {game.release_date.strftime('%b %d, %Y')}"
            if game.release_date
            else ""
        )

        return (
            f"<b>{game.name}</b>\n\n"
            f"{game.short_description or ''}\n\n"
            f"<b>Genres:</b> {genres}\n"
            f"<b>Developers:</b> {devs}\n"
            f"<b>Tags:</b> {tags}\n"
            f"<b>Platforms:</b> {', '.join([p for p, v in game.platforms.model_dump().items() if v])}\n"
            f"<b>Status:</b> {release}\n"
            f"<b>Price:</b> {price}\n\n"
            f"🔗 <a href='https://store.steampowered.com/app/{game.steam_appid}'>View on Steam</a>"
        )

    def _render_discount_post(self, disc: DiscountPublicationSchema) -> str:
        return (
            f"🔥 <b>Big Discount!</b>\n\n"
            f"<b>{disc.name}</b>\n"
            f"💸 {disc.old_price:.2f}$ → <b>{disc.new_price:.2f}$</b> ({disc.percent_drop:.0f}% off!)\n"
            f"🎮 Genres: {', '.join(disc.genres) if disc.genres else 'Unknown'}\n\n"
            f"<a href='https://store.steampowered.com/app/{disc.steam_appid}'>Get the deal</a>"
        )

    def _render_news_post(self, news: NewsPublicationSchema) -> str:
        date_str = news.date.strftime("%b %d, %Y")
        snippet = (news.contents[:400] + "…") if len(news.contents) > 400 else news.contents
        return (
            f"📰 <b>{news.title}</b>\n\n"
            f"{snippet}\n\n"
            f"📅 {date_str}\n"
            f"🔗 <a href='{news.url}'>Read more</a>"
        )

    def _render_reddit_post(self, post: RedditPostPublicationSchema) -> str:
        link = f"https://www.reddit.com{post.permalink}" if post.permalink else post.url or ""
        upvotes = f"⬆️ {post.ups or 0}  💬 {post.num_comments or 0}"
        snippet = (post.selftext[:400] + "…") if post.selftext else post.extract_snippet or ""
        return (
            f"👾 <b>{post.title}</b>\n\n"
            f"{snippet}\n\n"
            f"{upvotes}\n"
            f"📎 <a href='{link}'>View on Reddit</a>"
        )
