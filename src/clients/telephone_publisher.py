from __future__ import annotations
from datetime import datetime
from typing import Optional
from telethon import TelegramClient
from telethon.errors import RPCError
from src.utils.retry import RetryPolicy
from src.utils.logging import get_logger
from src.config.settings import settings
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class TelethonPublisher:
    """
    User client publisher (Telethon) for sending messages
    to a bot, channel, or user on behalf of a real account.
    """

    def __init__(self) -> None:
        """The constructor of the TelethonPublisher class."""
        self._log = get_logger().bind(client="telethon")

        self._retry = RetryPolicy(
            retries=C.HTTP_MAX_RETRIES,
            base_delay=C.HTTP_RETRY_BACKOFF_BASE,
            max_delay=C.HTTP_RETRY_BACKOFF_MAX,
            retry_exceptions=(RPCError,),
        )

        # Initialize the Telethon client
        self._client = TelegramClient(
            C.TELETHON_SESSION,
            settings.TELETHON_API_ID,
            settings.TELETHON_API_HASH,
            request_retries=5,
            connection_retries=5,
            timeout=10,
        )

        self._is_connected = False

    @property
    def client(self) -> TelegramClient:
        """The client property of the TelethonPublisher class.
        :return: TelegramClient object
        """
        return self._client

    async def connect(self) -> None:
        """The connect method of the TelethonPublisher class."""
        if not self._is_connected:
            await self._client.connect()
            if not await self._client.is_user_authorized():
                raise RuntimeError(
                    "Telethon session not authorized. Run one-time login script to sign in."
                )
            self._is_connected = True
            self._log.info("telethon_connected")

    async def start(self) -> None:
        """The start method of the TelethonPublisher class to connect and start the client"""
        try:
            await self._client.start()
            self._log.info("telethon_started")
        except Exception as e:
            self._log.error("telethon_start_failed", error=str(e))

    async def close(self) -> None:
        """The close method of the TelethonPublisher class to disconnect the client"""
        await self._client.disconnect()
        self._is_connected = False

    async def send_message(
        self,
        target: str,
        text: str,
        schedule_time: Optional[datetime] = None,
        parse_mode: str = "html",
    ) -> Optional[int]:
        """
        Sends a text message to a channel, chat, or bot.

        :param target: channel/bot username, ID, or @username
        :param text: message text
        :param schedule_time: scheduled time
        :param parse_mode: html/markdown (Telethon converts it)
        """
        await self.connect()

        try:
            async def _send():
                return await self._client.send_message(
                    entity=target,
                    message=text,
                    parse_mode=parse_mode,
                    schedule=schedule_time,
                )

            msg = await self._retry.run(_send)
            self._log.info("telethon_msg_sent", target=target, msg_id=msg.id)
            return msg.id

        except Exception as e:
            self._log.error("telethon_send_failed", target=target, error=str(e))
            return None
