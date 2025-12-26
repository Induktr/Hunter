from telethon import TelegramClient, events
from config.settings import settings
from core.logger import logger
from brain.filters import ContentFilter
from brain.ai_client import ai_client
from mouth.notifier import notifier

class Listener:
    """
    Telethon client to listen for new messages in specified channels.
    """
    def __init__(self):
        self.client = TelegramClient('hunter_session', settings.API_ID, settings.API_HASH)
        self.channels = settings.get_channels()

    async def start(self):
        logger.info(f"Starting listener for channels: {self.channels}")
        
        # Обработка событий подключения/отключения
        @self.client.on(events.Raw)
        async def raw_handler(update):
            pass # Можно использовать для отладки

        @self.client.on(events.NewMessage(chats=self.channels))
        async def handler(event):
            text = event.message.message
            if not text:
                return

            # 1. Filter
            if not ContentFilter.check(text):
                return

            logger.info("New relevant vacancy found! Analyzing...")

            # 2. AI Analysis
            analysis = await ai_client.analyze_vacancy(text)
            if not analysis:
                return

            # 3. Score Check & Notify
            if analysis.get("score", 0) >= 7:
                logger.info(f"Vacancy score {analysis['score']} >= 7. Notifying...")
                
                # Construct link
                chat = await event.get_chat()
                link = f"https://t.me/{chat.username}/{event.message.id}" if hasattr(chat, 'username') and chat.username else f"https://t.me/c/{str(chat.id)[4:]}/{event.message.id}"
                
                await notifier.send_vacancy_alert(analysis, link)

        await self.client.start()
        logger.info("✅ Telegram Listener is connected and running.")
        await self.client.run_until_disconnected()

listener = Listener()
