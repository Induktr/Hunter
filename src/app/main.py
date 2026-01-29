import asyncio
import sys
from src.shared.core.logger import logger
from src.shared.api.telegram_listener import tg_listener
from src.entities.ears.linkedin_listener import linkedin_listener
from src.entities.ears.djinni_listener import djinni_listener
from src.entities.ears.upwork_listener import upwork_listener

# Research imports
from src.sensors.search_engine import search_engine
from src.brain.ai_client import ai_researcher
from src.shared.utils.excel_manager import excel_manager

async def run_research(topic: str):
    """ Runs a one-off research task from CLI. """
    logger.info(f"CLI Research mode triggered: {topic}")
    search_data = await search_engine.search(topic)
    results = await ai_researcher.perform_research(topic, search_data['content'])
    if results:
        filepath = excel_manager.generate(results, filename=f"research_{topic.replace(' ', '_')}.xlsx")
        logger.info(f"Research complete. File saved to: {filepath}")
    else:
        logger.error("No results found.")

async def main():
    """
    Main entry point. Runs Telegram, LinkedIn, Djinni and Upwork listeners.
    """
    
    # Check for CLI research mode
    if len(sys.argv) > 1 and sys.argv[1] == "--research":
        topic = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Future of AI 2026"
        await run_research(topic)
        return

    logger.info("🚀 Hunter AI Job Sniper is starting (Researcher Mode ACTIVE)...")
    
    while True:
        try:
            # Запускаем все слушатели параллельно
            await asyncio.gather(
                tg_listener.start(),
                linkedin_listener.start(),
                djinni_listener.start(),
                upwork_listener.start()
            )
        except Exception as e:
            logger.error(f"Critical error in main loop: {e}")
            logger.info("Attempting to restart in 15 seconds...")
            await asyncio.sleep(15)
        except KeyboardInterrupt:
            logger.info("System stopped by user.")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System stopped by user.")
