import aiohttp
from typing import Optional
from src.utils.logging import get_logger


class TumblrClient:
    """Client for publishing posts to Tumblr using OAuth 2.0"""
    
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        oauth_token: str,
        oauth_token_secret: str,
        blog_identifier: str
    ):
        """
        Initialize Tumblr client with OAuth 1.0a credentials.
        
        :param consumer_key: Tumblr API consumer key
        :param consumer_secret: Tumblr API consumer secret
        :param oauth_token: OAuth token
        :param oauth_token_secret: OAuth token secret
        :param blog_identifier: Blog identifier (e.g., 'blogname.tumblr.com')
        """
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._oauth_token = oauth_token
        self._oauth_token_secret = oauth_token_secret
        self._blog_identifier = blog_identifier
        self._base_url = "https://api.tumblr.com/v2/blog"
        self._log = get_logger().bind(service="tumblr_client")
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def publish_text(
        self,
        title: str,
        body: str,
        tags: Optional[list[str]] = None,
        state: str = "published"
    ) -> Optional[str]:
        """
        Publish a text post to Tumblr.
        
        :param title: Post title
        :param body: Post body/content
        :param tags: List of tags
        :param state: Post state ('published', 'draft', 'queue', 'private')
        :return: Post ID if successful, None otherwise
        """
        session = await self._get_session()
        url = f"{self._base_url}/{self._blog_identifier}/post"
        
        params = {
            "type": "text",
            "title": title,
            "body": body,
            "state": state,
        }
        
        if tags:
            params["tags"] = ",".join(tags)
        
        try:
            async with session.post(
                url,
                params=params,
                headers=self._get_auth_headers("POST", url, params)
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    post_id = data.get("response", {}).get("id")
                    self._log.info("text_post_published", post_id=post_id, title=title)
                    return str(post_id)
                else:
                    error_text = await response.text()
                    self._log.error("text_post_failed", status=response.status, error=error_text)
                    return None
        except Exception as e:
            self._log.error("text_post_error", error=str(e))
            return None
    
    async def publish_photo(
        self,
        caption: str,
        photo_url: str,
        tags: Optional[list[str]] = None,
        state: str = "published"
    ) -> Optional[str]:
        """
        Publish a photo post to Tumblr.
        
        :param caption: Photo caption
        :param photo_url: URL of the photo
        :param tags: List of tags
        :param state: Post state ('published', 'draft', 'queue', 'private')
        :return: Post ID if successful, None otherwise
        """
        session = await self._get_session()
        url = f"{self._base_url}/{self._blog_identifier}/post"
        
        params = {
            "type": "photo",
            "caption": caption,
            "source": photo_url,
            "state": state,
        }
        
        if tags:
            params["tags"] = ",".join(tags)
        
        try:
            async with session.post(
                url,
                params=params,
                headers=self._get_auth_headers("POST", url, params)
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    post_id = data.get("response", {}).get("id")
                    self._log.info("photo_post_published", post_id=post_id)
                    return str(post_id)
                else:
                    error_text = await response.text()
                    self._log.error("photo_post_failed", status=response.status, error=error_text)
                    return None
        except Exception as e:
            self._log.error("photo_post_error", error=str(e))
            return None
    
    async def publish_link(
        self,
        title: str,
        url: str,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        state: str = "published"
    ) -> Optional[str]:
        """
        Publish a link post to Tumblr.
        
        :param title: Link title
        :param url: Target URL
        :param description: Link description
        :param tags: List of tags
        :param state: Post state ('published', 'draft', 'queue', 'private')
        :return: Post ID if successful, None otherwise
        """
        session = await self._get_session()
        post_url = f"{self._base_url}/{self._blog_identifier}/post"
        
        params = {
            "type": "link",
            "title": title,
            "url": url,
            "state": state,
        }
        
        if description:
            params["description"] = description
        
        if tags:
            params["tags"] = ",".join(tags)
        
        try:
            async with session.post(
                post_url,
                params=params,
                headers=self._get_auth_headers("POST", post_url, params)
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    post_id = data.get("response", {}).get("id")
                    self._log.info("link_post_published", post_id=post_id, title=title)
                    return str(post_id)
                else:
                    error_text = await response.text()
                    self._log.error("link_post_failed", status=response.status, error=error_text)
                    return None
        except Exception as e:
            self._log.error("link_post_error", error=str(e))
            return None
    
    def _get_auth_headers(self, method: str, url: str, params: dict) -> dict:
        """
        Generate OAuth 1.0a headers for authentication.
        Note: This is a simplified version. For production, use a proper OAuth library.
        """
        # For simplicity, this returns basic headers. In production, use:
        # - requests-oauthlib
        # - OAuth1 from requests_oauthlib
        # - Or implement full OAuth 1.0a signature generation
        
        # This is a placeholder - implement proper OAuth 1.0a
        return {
            "Content-Type": "application/x-www-form-urlencoded",
        }
