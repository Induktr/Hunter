from telethon import TelegramClient, events
from src.shared.config.settings import settings
from src.shared.core.logger import logger
from src.features.brain.filters import ContentFilter
from src.shared.api.ai_client import ai_client
from src.features.mouth.notifier import notifier

# Research Engine imports
from src.sensors.search_engine import search_engine
from src.brain.ai_client import ai_researcher
from src.shared.utils.excel_manager import excel_manager

class TGListener:
    """
    Telethon client to listen for new messages and research commands.
    """
    def __init__(self):
        self.client = TelegramClient('hunter_session', settings.API_ID, settings.API_HASH)
        self.channels = settings.get_channels()

    async def start(self):
        logger.info(f"Starting listener for channels: {self.channels}")
        
        # 1. Research command handler (for Admin ONLY)
        @self.client.on(events.NewMessage(pattern='/research (.*)', from_users=[settings.ADMIN_ID]))
        async def research_handler(event):
            topic = event.pattern_match.group(1)
            logger.info(f"Admin triggered research: {topic}")
            await event.respond(f"🔍 Starting deep research on: **{topic}**...")
            
            try:
                # Web Search
                search_data = await search_engine.search(topic)
                
                # AI Analysis
                await event.respond("🧠 Analyzing search results with AI...")
                results = await ai_researcher.perform_research(topic, search_data['content'])
                
                if not results:
                    await event.respond("❌ Sorry, I couldn't find structured data for this topic.")
                    return

                # Excel Generation
                await event.respond("📊 Generating Excel report...")
                filepath = excel_manager.generate(results, filename=f"research_{topic.replace(' ', '_')}.xlsx")
                
                if filepath:
                    await notifier.send_research_report(filepath, topic)
                else:
                    await event.respond("❌ Error generating Excel file.")
                    
            except Exception as e:
                logger.error(f"Error in research command: {e}")
                await event.respond(f"❌ Critical error during research: {e}")

        # 2. Vacancy Listener
        @self.client.on(events.NewMessage(chats=self.channels))
        async def handler(event):
            text = event.message.message
            if not text:
                return

            # Skip command messages
            if text.startswith('/'):
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

tg_listener = TGListener()
