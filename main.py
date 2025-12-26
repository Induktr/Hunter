import asyncio
from core.logger import logger
from ears.listener import listener
from mouth.notifier import notifier

async def main():
    """
    Main entry point. Runs both Telethon and Aiogram events if needed.
    """
    logger.info("🚀 Hunter AI Job Sniper is starting...")
    
    # --- TEST BLOCK ---
    # Sending a test notification to verify connectivity and formatting
    logger.info("Sending test notification to admin...")
    test_data = {
        "score": 10,
        "company": "TEST COMPANY (Hunter AI)",
        "salary": "$5000 - $8000",
        "cover_letter": "Здається, ви шукаєте ідеальний тест... Чи буде критично, если все запрацює з першого разу?",
        "red_flags": ["Test Flag 1", "Everything looks too good"]
    }
    await notifier.send_vacancy_alert(test_data, "https://github.com/google/antigravity")
    # ------------------
    
    while True:
        try:
            await listener.start()
        except Exception as e:
            logger.error(f"Critical error in main loop: {e}")
            logger.info("Attempting to restart in 10 seconds...")
            await asyncio.sleep(10)
        except KeyboardInterrupt:
            logger.info("System stopped by user.")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System stopped by user.")
