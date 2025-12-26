import asyncio
from core.logger import logger
from ears.listener import listener
from ears.linkedin_listener import linkedin_listener
from ears.djinni_listener import djinni_listener
from ears.upwork_listener import upwork_listener

async def main():
    """
    Main entry point. Runs Telegram, LinkedIn, Djinni and Upwork listeners.
    """
    logger.info("🚀 Hunter AI Job Sniper is starting (TG + LI + DJ + UP)...")
    
    while True:
        try:
            # Запускаем все слушатели параллельно
            await asyncio.gather(
                listener.start(),
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
