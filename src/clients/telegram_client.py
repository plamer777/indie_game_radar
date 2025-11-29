from __future__ import annotations
from datetime import datetime
import httpx
from src.utils.retry import RetryPolicy
from src.utils.logging import get_logger
from src.config.settings import settings
from typing import Optional, Union
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class TelegramPublisher:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=C.HTTP_TIMEOUT_SECONDS)
        self._retry = RetryPolicy(
            retries=C.HTTP_MAX_RETRIES,
            base_delay=C.HTTP_RETRY_BACKOFF_BASE,
            max_delay=C.HTTP_RETRY_BACKOFF_MAX,
            retry_exceptions=(httpx.HTTPError,),
        )
        self._token = settings.TELEGRAM_BOT_TOKEN
        self._chat_id = settings.TELEGRAM_CHAT_ID
        self._log = get_logger().bind(client="telegram")
        self._base_url = f'https://api.telegram.org/bot{self._token}'

    async def close(self):
        await self._client.aclose()

    async def post(
        self, endpoint: str,
        payload_json: dict | None = None, data: dict | None = None, files: dict | None = None
    ) -> str:
        url = f'{self._base_url}/{endpoint}'
        res = await self._client.post(url, json=payload_json, data=data, files=files)
        data = res.json()
        if not data.get("ok"):
            raise httpx.HTTPError(f"Telegram API error: {data}")
        return str(data["result"]["message_id"])

    async def publish_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        preview: bool = True,
        schedule_time: Optional[datetime] = None
    ) -> Optional[str]:
        """Публикует или планирует сообщение в Telegram"""
        payload = {
            "chat_id": self._chat_id, "text": text, "disable_web_page_preview": not preview,
            "parse_mode": parse_mode, "schedule_date": int(schedule_time.timestamp()) if schedule_time else None
        }

        try:
            msg_id = await self._retry.run(self.post, endpoint='sendMessage', payload_json=payload)
            self._log.info("tg_published", msg_id=msg_id)
            return msg_id
        except Exception as e:
            self._log.error("tg_publish_failed", error=str(e))
            return None

    async def publish_video(
        self,
        video: Union[str, bytes],
        caption: Optional[str] = None,
        parse_mode: str = "HTML",
        preview: bool = True,
        schedule_time: Optional[datetime] = None,
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Optional[str]:
        """
        Публикует видео в Telegram.
        :param video: URL на видео или байты (например, BytesIO.getvalue())
        :param caption: Подпись к ролику
        :param parse_mode: HTML или MarkdownV2
        :param preview: Показывать ли предпросмотр ссылок
        :param schedule_time: Плановое время публикации (если поддерживается)
        :param duration: Длительность ролика
        :param width: Ширина ролика
        :param height: Высота ролика
        """

        if isinstance(video, str):
            files = None
            data = {"video": video}
        else:
            files = {"video": ("video.mp4", video, "video/mp4")}
            data = {}

        data.update({
            "chat_id": self._chat_id,
            "caption": caption or "",
            "parse_mode": parse_mode,
            "disable_web_page_preview": not preview,
        })

        if duration:
            data["duration"] = duration
        if width:
            data["width"] = width
        if height:
            data["height"] = height

        if schedule_time:
            data["schedule_date"] = int(schedule_time.timestamp())

        try:
            msg_id = await self._retry.run(self.post, endpoint='sendVideo', data=data, files=files)
            self._log.info("tg_video_published", msg_id=msg_id)
            return msg_id
        except Exception as e:
            self._log.error("tg_video_publish_failed", error=str(e))
            return None

    async def publish_poll(
        self,
        question: str,
        options: list[str],
        is_anonymous: bool = True,
        allows_multiple_answers: bool = False,
        schedule_time: Optional[datetime] = None
    ) -> Optional[str]:
        """
        Публикует опрос в Telegram.
        :param question: текст вопроса
        :param options: список вариантов (2–10 вариантов)
        :param is_anonymous: анонимный ли опрос
        :param allows_multiple_answers: можно ли выбирать несколько вариантов
        :param schedule_time: плановая дата публикации
        """

        payload = {
            "chat_id": self._chat_id,
            "question": question,
            "options": options,
            "is_anonymous": is_anonymous,
            "allows_multiple_answers": allows_multiple_answers,
        }

        if schedule_time:
            payload["schedule_date"] = int(schedule_time.timestamp())

        try:
            msg_id = await self._retry.run(self.post, endpoint='sendPoll', payload_json=payload)
            self._log.info("tg_poll_published", msg_id=msg_id)
            return msg_id

        except Exception as e:
            self._log.error("tg_poll_publish_failed", error=str(e))

            return None

    async def publish_photo(
        self,
        photo: Union[str, bytes],
        caption: Optional[str] = None,
        parse_mode: str = "HTML",
        preview: bool = True,
        schedule_time: Optional[datetime] = None
    ) -> Optional[str]:
        """
        Публикует изображение с подписью в Telegram.
        :param photo: URL картинки, либо байты изображения (например, из BytesIO)
        :param caption: Подпись под фото (текст поста)
        :param parse_mode: Форматирование ('HTML' или 'MarkdownV2')
        :param preview: Показывать ли предпросмотр ссылок
        :param schedule_time: Плановая дата публикации (если поддерживается)
        """

        # Если передан URL
        if isinstance(photo, str):
            files = None
            data = {"photo": photo}
        else:
            # Переданы байты изображения
            files = {"photo": ("image.jpg", photo, "image/jpeg")}
            data = {}

        data.update({
            "chat_id": self._chat_id,
            "caption": caption or "",
            "parse_mode": parse_mode,
            "disable_web_page_preview": not preview,
        })

        if schedule_time:
            data["schedule_date"] = int(schedule_time.timestamp())

        try:
            msg_id = await self._retry.run(self.post, endpoint='sendPhoto', data=data, files=files)
            self._log.info("tg_photo_published", msg_id=msg_id)
            return msg_id
        except Exception as e:
            self._log.error("tg_photo_publish_failed", error=str(e))
            return None
