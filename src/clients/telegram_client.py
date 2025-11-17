from __future__ import annotations
from datetime import datetime
import httpx
from src.utils.retry import RetryPolicy
from src.utils.logging import get_logger
from src.config.settings import settings
from typing import Optional, Union
# ---------------------------------------------------------------------------------------------------------------------


class TelegramPublisher:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)
        self._retry = RetryPolicy(
            retries=settings.HTTP_MAX_RETRIES,
            base_delay=settings.HTTP_RETRY_BACKOFF_BASE,
            max_delay=settings.HTTP_RETRY_BACKOFF_MAX,
            retry_exceptions=(httpx.HTTPError,),
        )
        self._token = settings.TELEGRAM_BOT_TOKEN
        self._chat_id = settings.TELEGRAM_CHAT_ID
        self._log = get_logger().bind(client="telegram")

    async def close(self):
        await self._client.aclose()

    async def publish_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        preview: bool = True,
        schedule_time: Optional[datetime] = None
    ) -> Optional[str]:
        """Публикует или планирует сообщение в Telegram"""
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {
            "chat_id": self._chat_id, "text": text, "disable_web_page_preview": not preview,
            "parse_mode": parse_mode, "schedule_date": int(schedule_time.timestamp()) if schedule_time else None
        }

        # поддержка отложенной публикации

        async def _do():
            res = await self._client.post(url, json=payload)
            data = res.json()
            if not data.get("ok"):
                raise httpx.HTTPError(f"Telegram API error: {data}")
            return str(data["result"]["message_id"])

        try:
            msg_id = await self._retry.run(_do)
            self._log.info("tg_published", msg_id=msg_id)
            return msg_id
        except Exception as e:
            self._log.error("tg_publish_failed", error=str(e))
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
        url = f"https://api.telegram.org/bot{self._token}/sendPhoto"

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

        async def _do():
            res = await self._client.post(url, data=data, files=files)
            data_res = res.json()
            if not data_res.get("ok"):
                raise httpx.HTTPError(f"Telegram API error: {data_res}")
            return str(data_res["result"]["message_id"])

        try:
            msg_id = await self._retry.run(_do)
            self._log.info("tg_photo_published", msg_id=msg_id)
            return msg_id
        except Exception as e:
            self._log.error("tg_photo_publish_failed", error=str(e))
            return None
