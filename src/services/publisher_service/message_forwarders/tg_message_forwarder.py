from __future__ import annotations
from telethon import events
from src.clients import TelethonPublisher
from src.config.settings import settings
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class TelegramAutoForwarder:
    """
    A separate Telethon client that:
    - listens to messages from a channel/chat
    - automatically forwards them to a bot or another channel
    """

    def __init__(
        self, source_channel: str = settings.SOURCE_CHANNEL_USERNAME, 
        target_channel: str = settings.TARGET_BOT_USERNAME
    ) -> None:
        """The constructor of the TelegramAutoForwarder class.

        :param source_channel: source channel username to forward messages from
        :param target_channel: target channel username to forward messages to
        """
        self._source_channel = source_channel  # e.g. "@indie_gameradar"
        self._target = target_channel              # e.g. "@MyForwarderBot"

        self._log = get_logger().bind(forwarder='Message_forwarder')
        self._publisher = TelethonPublisher()

    async def start(self) -> None:
        """The method serves to start the forwarder to listen for new messages."""
        await self._publisher.start()
        client = self._publisher.client

        me = await client.get_me()
        self._log.info("listener_started", user=me.username)

        # Subscribe to new channel messages
        @client.on(events.NewMessage(chats=self._source_channel))
        async def handler(event: events.NewMessage.Event) -> None:
            """The function serves to handle new messages in the source channel
            :param event: event object containing the message to forward
            """
            try:
                msg = event.message
                text = msg.message or ""

                self._log.info("new_post_detected", source=self._source_channel, text_preview=text[:50])

                # Forward the message
                await self._publisher.client.forward_messages(
                    self._target,
                    msg,
                    from_peer=msg.peer_id
                )

            except Exception as e:
                self._log.error("forward_failed", error=str(e))

        self._log.info("listener_running")
        await client.run_until_disconnected()
