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
    # LinkedIn Settings
    LINKEDIN_KEYWORDS: list[str] = ["Junior React", "Junior Frontend", "Junior JavaScript"]
    LINKEDIN_LOCATION: str = "Europe" # Changed location to Europe as an example, feel free to change
    
    # Djinni Settings
    DJINNI_KEYWORDS: list[str] = ["JavaScript", "React", "Frontend"]

    # Upwork Settings
    UPWORK_KEYWORDS: list[str] = ["React", "Next.js", "TypeScript"]
    UPWORK_COOKIE: str = os.getenv("UPWORK_COOKIE", "")
    UPWORK_MIN_CONNECTS: int = 15
    
    CHANNELS_FILE: Path = Path(__file__).parent / "channels.json"

    def get_channels(self) -> list[int]:
        if not self.CHANNELS_FILE.exists():
            return []
        with open(self.CHANNELS_FILE, "r") as f:
            return json.load(f)

settings = Settings()
