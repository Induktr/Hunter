import os
import itertools
from google import genai
from src.shared.config.settings import settings
from src.shared.core.logger import logger

class GeminiKeyPool:
    """
    Round-robin API Key Pool for Google Gemini.
    Multiplies rate-limits by rotating across multiple free API keys.
    Supports comma-separated keys in GEMINI_KEY (e.g. key1,key2,key3).
    """
    def __init__(self):
        raw_keys = settings.GEMINI_KEY or os.getenv("GEMINI_KEY", "")
        # Parse comma-separated or single keys
        self.keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        
        if not self.keys:
            logger.warning("⚠️ GeminiKeyPool: No GEMINI_KEY configured!")
            self.clients = []
        else:
            self.clients = [genai.Client(api_key=key) for key in self.keys]
            logger.info(f"🔑 GeminiKeyPool: Initialized with {len(self.clients)} active API key(s). Total RPM capacity: {len(self.clients) * 15} RPM.")
        
        self._cycler = itertools.cycle(self.clients) if self.clients else None

    def get_client(self) -> genai.Client:
        """ Returns the next client in round-robin sequence. """
        if not self._cycler:
            # Fallback single client
            return genai.Client(api_key=settings.GEMINI_KEY)
        return next(self._cycler)

    @property
    def key_count(self) -> int:
        return len(self.clients)

gemini_key_pool = GeminiKeyPool()
