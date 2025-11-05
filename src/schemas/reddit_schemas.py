from pydantic import Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from src.schemas.base import BaseSchema
# ---------------------------------------------------------------------------------------------------------------------


class RedditPostSchema(BaseSchema):
    reddit_id: str = Field(..., description="ID поста (например '1oc22gq')")
    fullname: Optional[str] = Field(None, description="Полное имя (например t3_1oc22gq)")
    steam_appid: Optional[int] = Field(None, description="Steam AppID, если удаётся извлечь из ссылки")
    game_name: Optional[str] = Field(None, description="Название игры, если извлечено вручную или via сопоставление")
    type: Literal['game_related', 'game_dev_story'] = Field(..., description="Тип поста")
    title: str = Field(..., description="Заголовок поста")
    selftext: Optional[str] = Field(None, description="Текст поста (для self-post)")
    selftext_html: Optional[str] = Field(None, description="HTML версия текста, если доступна")
    url: Optional[str] = Field(None, description="URL, на который указывает пост или сайт статьи")
    permalink: Optional[str] = Field(None, description="Постоянная ссылка Reddit (например https://reddit.com/…)")
    domain: Optional[str] = Field(None, description="Домен ссылки (например store.steampowered.com)")

    author: Optional[str] = Field(None, description="Имя автора (u/имя)")
    author_fullname: Optional[str] = Field(None, description="fullname автора (например t2_xxx)")
    author_is_blocked: Optional[bool] = Field(None, description="True если автор заблокирован")
    author_premium: Optional[bool] = Field(None, description="True если автор имеет Reddit Premium")

    subreddit: str = Field(..., description="Название сабреддита (например 'IndieGaming')")
    subreddit_id: Optional[str] = Field(None, description="ID сабреддита (например t5_2r0e3)")
    subreddit_name_prefixed: Optional[str] = Field(None, description="Пример: 'r/IndieGaming'")
    subreddit_type: Optional[str] = Field(None, description="Тип сабреддита публичный/private и т.п.")
    subreddit_subscribers: Optional[int] = Field(None, description="Число подписчиков сабреддита, если доступно")

    created_utc: datetime = Field(..., description="Время создания (utc)")
    edited_utc: Optional[datetime] = Field(None, description="Время редактирования, если было")

    score: int = Field(..., description="Количество очков (upvotes-downvotes)")
    ups: Optional[int] = Field(None, description="Количество up-votes (если доступно)")
    downs: Optional[int] = Field(None, description="Количество down-votes (если доступно)")
    upvote_ratio: Optional[float] = Field(None, description="Соотношение up-votes к общему числу голосов")

    num_comments: int = Field(..., description="Количество комментариев")
    num_crossposts: Optional[int] = Field(None, description="Количество кросспостов (если доступно)")

    over_18: bool = Field(..., description="True если пост NSFW")
    is_self: bool = Field(..., description="True если self-post (текстовый)")
    is_video: bool = Field(..., description="True если видео-пост")
    is_original_content: Optional[bool] = Field(None, description="True если контент отмечен как оригинальный")

    thumbnail: Optional[str] = Field(None, description="URL миниатюры")
    thumbnail_height: Optional[int] = Field(None, description="Высота миниатюры, если есть")
    thumbnail_width: Optional[int] = Field(None, description="Ширина миниатюры, если есть")

    preview_images: Optional[List[str]] = Field(None, description="Список URL изображений/гифок из preview")
    media_urls: Optional[List[str]] = Field(None, description="Ссылки на медиа-ресурсы (secure_media, media_embed и т.п.)")

    total_awards_received: Optional[int] = Field(None, description="Общее число наград, присуждённых посту")
    all_awardings: Optional[List[Dict[str, Any]]] = Field(None, description="Детали наград (список словарей)")

    post_hint: Optional[str] = Field(None, description="Подсказка формата поста (например 'link', 'image', 'video')")
    link_flair_text: Optional[str] = Field(None, description="Текст флейра ссылки")
    link_flair_template_id: Optional[str] = Field(None, description="ID шаблона флейра ссылки")

    extract_snippet: Optional[str] = Field(None, description="Короткая выдержка из selftext, пригодная для цитаты")

    crawl_time: datetime = Field(default_factory=datetime.now, description="Время скачивания/сохранения записи")

    class Config:
        from_attributes = True


class RankedRedditPostSchema(RedditPostSchema):
    last_score: Optional[float] = None
    last_ranked_at: datetime = Field(default_factory=datetime.now)
