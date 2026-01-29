import asyncio
from src.app.main import main
from src.shared.core.logger import logger

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        logger.error(f"System stopped by user: {e}")