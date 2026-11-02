from src.schemas import AllocatedPostsSchema
from src.utils.common import clean_text


class TumblrPostRenderer:
    """Renderer for formatting posts for Tumblr publication"""
    
    def render(self, record: AllocatedPostsSchema) -> tuple[str, str, list[str]]:
        """
        Render post for Tumblr.
        
        :param record: Allocated post record
        :return: Tuple of (title, body, tags)
        """
        category = record.category
        
        if category == 'games':
            return self._render_game(record)
        elif category == 'news':
            return self._render_news(record)
        elif category == 'reddit_posts':
            return self._render_reddit_post(record)
        elif category == 'reddit_memes':
            return self._render_reddit_meme(record)
        elif category == 'discounts':
            return self._render_discount(record)
        elif category == 'reviews':
            return self._render_review(record)
        elif category == 'game_leaderboards':
            return self._render_leaderboard(record)
        else:
            raise ValueError(f"Unsupported category for Tumblr: {category}")
    
    def _render_game(self, record: AllocatedPostsSchema) -> tuple[str, str, list[str]]:
        """Render game post for Tumblr"""
        post = record.post
        
        title = post.name
        
        # Build body with HTML formatting for Tumblr
        body_parts = []
        
        if post.header_image:
            body_parts.append(f'<img src="{post.header_image}" alt="{post.name}"/>')
        
        if post.short_description:
            body_parts.append(f"<p>{clean_text(post.short_description)}</p>")
        
        if post.detailed_description:
            body_parts.append(f"<p>{clean_text(post.detailed_description)}</p>")
        
        # Add genres and tags
        if post.genres:
            body_parts.append(f"<p><strong>Genres:</strong> {', '.join(post.genres)}</p>")
        
        # Add price if available
        if post.price and not post.is_free:
            body_parts.append(f"<p><strong>Price:</strong> ${post.price.final:.2f}</p>")
        elif post.is_free:
            body_parts.append("<p><strong>Price:</strong> Free to Play</p>")
        
        # Add Steam link
        if post.steam_appid:
            body_parts.append(f'<p><a href="https://store.steampowered.com/app/{post.steam_appid}">View on Steam</a></p>')
        
        # Generate tags
        tags = self._generate_tags(post)
        
        return title, "\n".join(body_parts), tags
    
    def _render_news(self, record: AllocatedPostsSchema) -> tuple[str, str, list[str]]:
        """Render news post for Tumblr"""
        post = record.post
        
        title = post.title or "Gaming News"
        
        body_parts = []
        
        if post.title:
            body_parts.append(f"<h2>{post.title}</h2>")
        
        if post.contents:
            body_parts.append(f"<p>{clean_text(post.contents)}</p>")
        
        if post.url:
            body_parts.append(f'<p><a href="{post.url}">Read more</a></p>')
        
        if post.appid:
            body_parts.append(f'<p><a href="https://store.steampowered.com/app/{post.appid}">View on Steam</a></p>')
        
        tags = ["news", "gaming"]
        if post.feedlabel:
            tags.append(post.feedlabel.lower())
        
        return title, "\n".join(body_parts), tags
    
    def _render_reddit_post(self, record: AllocatedPostsSchema) -> tuple[str, str, list[str]]:
        """Render Reddit post for Tumblr"""
        post = record.post
        
        title = post.title or "Reddit Post"
        
        body_parts = []
        
        body_parts.append(f"<h2>{post.title}</h2>")
        
        if post.selftext:
            body_parts.append(f"<p>{clean_text(post.selftext)}</p>")
        
        if post.url:
            body_parts.append(f'<p><a href="{post.url}">Source</a></p>')
        
        if post.permalink:
            body_parts.append(f'<p><a href="https://reddit.com{post.permalink}">View on Reddit</a></p>')
        
        if post.subreddit:
            body_parts.append(f"<p>Posted in r/{post.subreddit}</p>")
        
        tags = ["reddit", post.subreddit.lower()] if post.subreddit else ["reddit"]
        
        return title, "\n".join(body_parts), tags
    
    def _render_reddit_meme(self, record: AllocatedPostsSchema) -> tuple[str, str, list[str]]:
        """Render Reddit meme for Tumblr"""
        post = record.post
        
        title = post.title or "Gaming Meme"
        
        body_parts = []
        
        body_parts.append(f"<h2>{post.title}</h2>")
        
        # Use the first preview image or URL
        image_url = post.url or (post.preview_images[0] if post.preview_images else None)
        if image_url:
            body_parts.append(f'<img src="{image_url}" alt="{post.title}"/>')
        
        if post.permalink:
            body_parts.append(f'<p><a href="https://reddit.com{post.permalink}">View on Reddit</a></p>')
        
        tags = ["meme", "gaming", "reddit"]
        
        return title, "\n".join(body_parts), tags
    
    def _render_discount(self, record: AllocatedPostsSchema) -> tuple[str, str, list[str]]:
        """Render discount post for Tumblr"""
        post = record.post
        
        title = f"🎮 {post.name} - {post.percent_drop}% OFF!"
        
        body_parts = []
        
        if post.header_image:
            body_parts.append(f'<img src="{post.header_image}" alt="{post.name}"/>')
        
        body_parts.append(f"<h2>{post.name}</h2>")
        body_parts.append(f"<p><strong>Discount:</strong> {post.percent_drop}% OFF</p>")
        body_parts.append(f"<p><strong>Old Price:</strong> ${post.old_price:.2f}</p>")
        body_parts.append(f"<p><strong>New Price:</strong> ${post.new_price:.2f}</p>")
        body_parts.append(f"<p><strong>You Save:</strong> ${post.absolute_drop:.2f}</p>")
        
        if post.steam_appid:
            body_parts.append(f'<p><a href="https://store.steampowered.com/app/{post.steam_appid}">Get it on Steam</a></p>')
        
        tags = ["discount", "sale", "gaming"]
        
        return title, "\n".join(body_parts), tags
    
    def _render_review(self, record: AllocatedPostsSchema) -> tuple[str, str, list[str]]:
        """Render review post for Tumblr"""
        post = record.post
        
        title = f"🎮 {post.game_name} - Review"
        
        body_parts = []
        
        if post.image:
            body_parts.append(f'<img src="{post.image}" alt="{post.game_name}"/>')
        
        body_parts.append(f"<h2>{post.game_name}</h2>")
        
        if post.total_reviews:
            body_parts.append(f"<p><strong>Total Reviews:</strong> {post.total_reviews}</p>")
        
        if post.review_score:
            body_parts.append(f"<p><strong>Review Score:</strong> {post.review_score}%</p>")
        
        if post.summary:
            if post.summary.title:
                body_parts.append(f"<h3>{post.summary.title}</h3>")
            if post.summary.summary:
                body_parts.append(f"<p>{clean_text(post.summary.summary)}</p>")
            
            if post.summary.strengths:
                body_parts.append("<p><strong>Strengths:</strong></p><ul>")
                for strength in post.summary.strengths:
                    body_parts.append(f"<li>{strength}</li>")
                body_parts.append("</ul>")
            
            if post.summary.weaknesses:
                body_parts.append("<p><strong>Weaknesses:</strong></p><ul>")
                for weakness in post.summary.weaknesses:
                    body_parts.append(f"<li>{weakness}</li>")
                body_parts.append("</ul>")
        
        if post.steam_appid:
            body_parts.append(f'<p><a href="https://store.steampowered.com/app/{post.steam_appid}">View on Steam</a></p>')
        
        tags = ["review", "gaming"]
        
        return title, "\n".join(body_parts), tags
    
    def _render_leaderboard(self, record: AllocatedPostsSchema) -> tuple[str, str, list[str]]:
        """Render leaderboard post for Tumblr"""
        post = record.post
        
        title = f"🏆 {post.game_name} - Speedrun Leaderboards"
        
        body_parts = []
        
        body_parts.append(f"<h2>{post.game_name}</h2>")
        body_parts.append(f"<p><strong>Release Date:</strong> {post.release_date.strftime('%Y-%m-%d')}</p>")
        
        if post.category_leaderboards:
            body_parts.append("<h3>Category Leaderboards</h3><ul>")
            for leaderboard in post.category_leaderboards:
                body_parts.append(f"<li><strong>{leaderboard.category}:</strong> {leaderboard.leader} ({leaderboard.time})</li>")
            body_parts.append("</ul>")
        
        if post.weblink:
            body_parts.append(f'<p><a href="{post.weblink}">View Leaderboards</a></p>')
        
        if post.discord:
            body_parts.append(f'<p><a href="{post.discord}">Join Discord</a></p>')
        
        tags = ["speedrun", "leaderboard", "gaming"]
        
        return title, "\n".join(body_parts), tags
    
    def _generate_tags(self, post) -> list[str]:
        """Generate tags from post data"""
        tags = ["indie", "gaming"]
        
        if post.genres:
            tags.extend([genre.lower() for genre in post.genres[:5]])
        
        if post.tags:
            tags.extend([tag.lower() for tag in post.tags[:5]])
        
        if post.developers:
            tags.extend([dev.lower() for dev in post.developers[:3]])
        
        # Remove duplicates and limit to 10 tags
        return list(set(tags))[:10]
