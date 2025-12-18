from __future__ import annotations
from telethon import events
from telethon.tl.custom import Message
from src.clients import TelethonPublisher
from src.config.settings import settings
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class TelegramAutoForwarder:
    """
    Отдельный Telethon-клиент, который:
    - слушает сообщения из канала/чата
    - автоматически пересылает их боту или другому каналу
    """

    def __init__(
        self, source_channel: str = settings.SOURCE_CHANNEL_USERNAME, 
        target_channel: str = settings.TARGET_BOT_USERNAME
    ) -> None:
        """The constructor of the TelegramAutoForwarder class.

        :param source_channel: source channel username to forward messages from
        :param target_channel: target channel username to forward messages to
        """
        self._source_channel = source_channel  # например: "@indie_gameradar"
        self._target = target_channel              # например: "@MyForwarderBot"

        self._api_id = settings.TELETHON_API_ID
        self._api_hash = settings.TELETHON_API_HASH
        self._log = get_logger().bind(forwarder='Message_forwarder')
        self._publisher = TelethonPublisher()

    async def start(self) -> None:
        """The method serves to start the forwarder to listen for new messages."""
        await self._publisher.start()
        client = self._publisher.client

        me = await client.get_me()
        self._log.info("listener_started", user=me.username)

        # Подписываемся на новые сообщения из канала
        @client.on(events.NewMessage(chats=self._source_channel))
        async def handler(event: events.NewMessage.Event) -> None:
            """The function serves to handle new messages in the source channel
            :param event: event object containing the message to forward
            """
            try:
                msg = event.message
                text = msg.message or ""

                self._log.info("new_post_detected", source=self._source_channel, text_preview=text[:50])

                # Пересылка контента (текст, фото, видео, документы)
                await self._forward_message(msg)

            except Exception as e:
                self._log.error("forward_failed", error=str(e))

        self._log.info("listener_running")
        await client.run_until_disconnected()

    async def _forward_message(self, msg: Message) -> None:
        """
        Унифицированная пересылка сообщения с контентом.
        """

        # Если это медиа — пересылаем через send_file
        if msg.media:
            self._log.info(f'Message type: {type(msg)}')
            file = await msg.download_media(bytes)
            if msg.photo and file:
                await self._publisher.send_photo(
                    target=self._target,
                    photo=await msg.download_media(bytes),
                    caption=msg.message or "",
                )
                return

            if msg.video and file:
                await self._publisher.send_video(
                    target=self._target,
                    video=await msg.download_media(bytes),
                    caption=msg.message or "",
                )
                return

            # другие файлы

            if file:
                await self._publisher._client.send_file(
                    self._target,
                    file=await msg.download_media(bytes),
                    caption=msg.message or "",
                )
                return

        # Если это только текст
        await self._publisher.send_message(
            target=self._target,
            text=msg.message or "",
        )
