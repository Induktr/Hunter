import asyncio
import time
from collections import deque
from src.shared.core.logger import logger
from src.brain.key_rotator import gemini_key_pool

class AsyncRateLimiter:
    """
    Sliding window rate limiter for Google Gemini Free Tier.
    Dynamically scales capacity based on the number of keys in GeminiKeyPool (12 RPM per key).
    """
    def __init__(self, base_rpm_per_key: int = 12, period_seconds: float = 60.0):
        self.base_rpm_per_key = base_rpm_per_key
        self.period_seconds = period_seconds
        self.timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    @property
    def max_requests(self) -> int:
        keys = max(1, gemini_key_pool.key_count)
        return self.base_rpm_per_key * keys

    async def acquire(self):
        """
        Waits proactively if the rate limit threshold is reached.
        """
        async with self._lock:
            now = time.monotonic()
            limit = self.max_requests
            
            # Remove timestamps outside the sliding window
            while self.timestamps and (now - self.timestamps[0]) >= self.period_seconds:
                self.timestamps.popleft()

            # If quota is full, calculate required pause
            if len(self.timestamps) >= limit:
                sleep_time = self.period_seconds - (now - self.timestamps[0]) + 0.1
                if sleep_time > 0:
                    logger.info(f"⏳ RateLimiter: Smoothing requests ({len(self.timestamps)}/{limit} RPM across {gemini_key_pool.key_count} key(s)). Pausing for {sleep_time:.1f}s...")
                    await asyncio.sleep(sleep_time)
                
                # Re-clean after waking up
                now = time.monotonic()
                while self.timestamps and (now - self.timestamps[0]) >= self.period_seconds:
                    self.timestamps.popleft()

            self.timestamps.append(time.monotonic())

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Shared dynamic rate limiter singleton
ai_rate_limiter = AsyncRateLimiter(base_rpm_per_key=12, period_seconds=60.0)
