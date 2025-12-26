import json
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    API_ID: int = os.getenv("API_ID", 0)
    API_HASH: str = os.getenv("API_HASH", "")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    GEMINI_KEY: str = os.getenv("GEMINI_KEY", "")
    ADMIN_ID: int = os.getenv("ADMIN_ID", 0)
    
    CHANNELS_FILE: Path = Path(__file__).parent / "channels.json"

    def get_channels(self) -> list[int]:
        if not self.CHANNELS_FILE.exists():
            return []
        with open(self.CHANNELS_FILE, "r") as f:
            return json.load(f)

settings = Settings()
