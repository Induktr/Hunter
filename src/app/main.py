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

async def supervised_listener(name: str, coro_func):
    """
    Supervisor wrapper: isolates each listener so that a crash in one
    (e.g., Telethon session issue) does not kill the other scrapers.
    """
    while True:
        try:
            logger.info(f"Starting listener: {name}")
            await coro_func()
        except Exception as e:
            logger.error(f"⚠️ Listener '{name}' encountered an error: {e}")
            logger.info(f"⏳ Listener '{name}' will restart in 30 seconds...")
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            logger.info(f"Listener '{name}' stopped.")
            break

async def main():
    """
    Main entry point. Runs Telegram, LinkedIn, Djinni and Upwork listeners concurrently with supervisor isolation.
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--research":
        topic = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Future of AI 2026"
        await run_research(topic)
        return

    logger.info("🚀 Hunter AI Job Sniper is starting (All Listeners Active)...")

    # Run all listeners with independent supervision
    await asyncio.gather(
        supervised_listener("Telegram Channel Listener", tg_listener.start),
        supervised_listener("Djinni.co Scraper", djinni_listener.start),
        supervised_listener("Upwork Scraper", upwork_listener.start),
        supervised_listener("LinkedIn Scraper", linkedin_listener.start),
        return_exceptions=True
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System stopped by user.")
