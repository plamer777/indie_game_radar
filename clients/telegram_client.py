from __future__ import annotations
import httpx
from utils.retry import RetryPolicy
from utils.logging import get_logger
from config.settings import settings
from models.game import GameModel
from models.igdb import IGDBMeta
from typing import Optional
from config import constants as C


class TelegramPublisher:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)
        self._retry = RetryPolicy(
            retries=settings.HTTP_MAX_RETRIES,
            base_delay=settings.HTTP_RETRY_BACKOFF_BASE,
            max_delay=settings.HTTP_RETRY_BACKOFF_MAX,
            retry_exceptions=(httpx.HTTPError,),
        )
        self._log = get_logger().bind(client="telegram")
        self._chat_id = settings.TELEGRAM_CHAT_ID
        self._token = settings.TELEGRAM_BOT_TOKEN

    async def close(self) -> None:
        await self._client.aclose()

    async def publish(self, game: GameModel, meta: Optional[IGDBMeta], score: float) -> Optional[str]:
        text = self._format_message(game, meta, score)
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "disable_web_page_preview": False,
            "parse_mode": "HTML",
        }

        async def _do():
            res = await self._client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            if not data.get("ok"):
                raise httpx.HTTPError(f"Telegram error: {data}")
            return str(data.get("result", {}).get("message_id"))

        try:
            message_id = await self._retry.run(_do)
            self._log.info("tg_published", appid=game.steam_appid, message_id=message_id)
            return message_id
        except Exception as e:
            self._log.error("tg_publish_failed", appid=game.steam_appid, error=str(e))
            return None

    def _format_message(self, game: GameModel, meta: Optional[IGDBMeta], score: float) -> str:
        parts = []
        parts.append(f"<b>{game.name}</b>")
        if meta and meta.summary:
            parts.append(meta.summary[:C.SUMMARY_MAX_LEN] + ("..." if len(meta.summary) > C.SUMMARY_MAX_LEN else ""))
        elif game.short_description:
            parts.append(game.short_description[:C.SUMMARY_MAX_LEN] + ("..." if len(game.short_description) > C.SUMMARY_MAX_LEN else ""))

        # price and discount
        price_str = C.PRICE_FREE_LABEL if game.is_free else (f"{game.price.final:.2f} {game.price.currency}" if game.price else C.PRICE_UNKNOWN_LABEL)
        if game.price and game.price.discount_percent:
            price_str += f" (−{int(game.price.discount_percent)}%)"
        parts.append(f"Price: {price_str}")

        # links
        steam_link = f"https://store.steampowered.com/app/{game.steam_appid}"
        parts.append(f"<a href=\"{steam_link}\">Steam</a>")
        if meta and meta.websites:
            parts.append(C.WEBSITE_SEPARATOR.join([f"<a href=\"{w}\">Website</a>" for w in meta.websites[:C.WEBSITES_MAX]]))

        parts.append(f"Score: {score:.{C.SCORE_DECIMALS}f}")
        return "\n".join(parts)
