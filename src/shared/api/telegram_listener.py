from telethon import TelegramClient, events
from src.shared.config.settings import settings
from src.shared.core.logger import logger
from src.features.brain.filters import ContentFilter
from src.shared.api.ai_client import ai_client
from src.features.mouth.notifier import notifier
from src.shared.utils.dedup_store import dedup_store

# Research Engine imports
from src.sensors.search_engine import search_engine
from src.brain.ai_client import ai_researcher
from src.shared.utils.excel_manager import excel_manager

class TGListener:
    """
    Real-time event-driven Telegram channel listener with persistent deduplication.
    Processes posts instantly as they appear, without polling delays.
    """
    def __init__(self):
        self.client = TelegramClient('hunter_session', settings.API_ID, settings.API_HASH)
        self.channels = settings.get_channels()

    async def start(self):
        logger.info(f"Starting real-time listener for channels: {self.channels}")
        
        # 1. Research command handler (for Admin ONLY)
        @self.client.on(events.NewMessage(pattern='/research (.*)', from_users=[settings.ADMIN_ID]))
        async def research_handler(event):
            topic = event.pattern_match.group(1)
            logger.info(f"Admin triggered research: {topic}")
            await event.respond(f"🔍 Starting deep research on: **{topic}**...")
            
            try:
                search_data = await search_engine.search(topic)
                await event.respond("🧠 Analyzing search results with AI...")
                results = await ai_researcher.perform_research(topic, search_data['content'])
                
                if not results:
                    await event.respond("❌ Sorry, I couldn't find structured data for this topic.")
                    return

                await event.respond("📊 Generating Excel report...")
                filepath = excel_manager.generate(results, filename=f"research_{topic.replace(' ', '_')}.xlsx")
                
                if filepath:
                    await notifier.send_research_report(filepath, topic)
                else:
                    await event.respond("❌ Error generating Excel file.")
                    
            except Exception as e:
                logger.error(f"Error in research command: {e}")
                await event.respond(f"❌ Critical error during research: {e}")

        # 2. Real-time Vacancy Listener
        @self.client.on(events.NewMessage(chats=self.channels))
        async def handler(event):
            text = event.message.message
            if not text:
                return

            if text.startswith('/'):
                return

            chat = await event.get_chat()
            chat_id_str = str(chat.id) if chat else "unknown"
            msg_id = f"tg_{chat_id_str}_{event.message.id}"

            # Persistent Deduplication Check (Saves quota on edited/forwarded messages)
            if await dedup_store.is_processed(msg_id):
                return
            
            await dedup_store.mark_processed(msg_id)

            # 1. Fast Content Filter (0 tokens)
            if not ContentFilter.check(text):
                return

            logger.info(f"Telegram: New candidate vacancy detected in channel {getattr(chat, 'title', chat_id_str)}! Analyzing...")

            # 2. 2-Stage Cascading AI Analysis (Fast Triage -> Deep TSD)
            analysis = await ai_client.analyze_vacancy(text)
            if not analysis:
                return

            # 3. Score Check & Real-time Alert
            if analysis.get("score", 0) >= 7:
                logger.info(f"🎯 Telegram vacancy score {analysis['score']} >= 7. Notifying...")
                link = f"https://t.me/{chat.username}/{event.message.id}" if hasattr(chat, 'username') and chat.username else f"https://t.me/c/{str(chat.id)[4:]}/{event.message.id}"
                await notifier.send_vacancy_alert(analysis, link)

        await self.client.start()
        logger.info("✅ Telegram Listener is connected and actively listening in real-time.")
        await self.client.run_until_disconnected()

tg_listener = TGListener()
