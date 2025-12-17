from __future__ import annotations
from datetime import datetime
from typing import Optional, Union
from qrcode.main import QRCode
from telethon import TelegramClient
from telethon.errors import RPCError, SessionPasswordNeededError
from src.utils.retry import RetryPolicy
from src.utils.logging import get_logger
from src.config.settings import settings
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class TelethonPublisher:
    """
    User Client publisher (Telethon) для отправки сообщений
    боту, каналу или пользователю от имени реального аккаунта.
    """

    def __init__(self) -> None:
        """The constructor of the TelethonPublisher class."""
        self._log = get_logger().bind(client="telethon")
        self._qr = QRCode()

        self._retry = RetryPolicy(
            retries=C.HTTP_MAX_RETRIES,
            base_delay=C.HTTP_RETRY_BACKOFF_BASE,
            max_delay=C.HTTP_RETRY_BACKOFF_MAX,
            retry_exceptions=(RPCError,),
        )

        # Инициализация Telethon-клиента
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

    async def create_tg_session(self) -> None:
        """The create_tg_session method of the TelethonPublisher class to create a new TG session"""

        def display_url_as_qr(url: str) -> None:
            """The method serves to visualise URL as QR code
            :param url: URL to visualise as QR code
            """
            print(url)
            self._qr.clear()
            self._qr.add_data(url)
            self._qr.print_ascii()

        async def run_cycle(client: TelegramClient) -> None:
            """The run_cycle method of the TelethonPublisher class to visualise QR code for authorization process
            :param client: TelegramClient to work with Telegram
            """
            if (not client.is_connected()):
                await client.connect()

            await client.connect()
            qr_login = await client.qr_login()

            r = False
            while not r:
                display_url_as_qr(qr_login.url)
                # Important! You need to wait for the login to complete!
                try:
                    r = await qr_login.wait()
                except SessionPasswordNeededError:
                    await client.sign_in(password='your_2fa_password')
                except:
                    try:
                        await qr_login.recreate()
                    except SessionPasswordNeededError:
                        await client.sign_in(password='your_2fa_password')

        await run_cycle(self._client)

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
        Отправляет текстовое сообщение в канал, чат или боту.

        :param target: username канала/бота, ID или @username
        :param text: текст
        :param schedule_time: время расписания
        :param parse_mode: html/markdown (Telethon сам конвертирует)
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

    async def send_photo(
        self,
        target: str,
        photo: Union[str, bytes],
        caption: Optional[str] = None,
        schedule_time: Optional[datetime] = None,
        parse_mode: str = "html",
    ) -> Optional[int]:
        """The methor serves to send a photo to the target channel, bot or user.

        :param target: username channel/bot/user, ID or @username
        :param photo: photo
        :param caption: caption
        :param schedule_time: schedule time
        :param parse_mode: html/markdown (Telethon сам конвертирует)
        """
        await self.connect()

        try:
            async def _send():
                return await self._client.send_file(
                    entity=target,
                    file=photo,
                    caption=caption,
                    parse_mode=parse_mode,
                    schedule=schedule_time,
                )

            msg = await self._retry.run(_send)
            self._log.info("telethon_photo_sent", msg_id=msg.id)
            return msg.id

        except Exception as e:
            self._log.error("telethon_photo_failed", error=str(e))
            return None

    async def send_video(
        self,
        target: str,
        video: Union[str, bytes],
        caption: Optional[str] = None,
        schedule_time: Optional[datetime] = None,
        parse_mode: str = "html",
    ) -> Optional[int]:
        """The method serves to send a video to the target channel, bot or user.

        :param target: username channel/bot/user, ID or @username
        :param video: video
        :param caption: caption
        :param schedule_time: schedule time
        :param parse_mode: html/markdown (Telethon сам конвертирует)
        """
        await self.connect()

        try:
            async def _send():
                return await self._client.send_file(
                    entity=target,
                    file=video,
                    caption=caption,
                    parse_mode=parse_mode,
                    schedule=schedule_time,
                    video_note=False,
                )

            msg = await self._retry.run(_send)
            self._log.info("telethon_video_sent", msg_id=msg.id)
            return msg.id

        except Exception as e:
            self._log.error("telethon_video_failed", error=str(e))
            return None
