import json
import os
import asyncio
from pathlib import Path
from src.shared.core.logger import logger

class DedupStore:
    """
    Persistent disk-backed deduplication store.
    Saves processed job IDs and URLs to disk to eliminate redundant AI calls across restarts.
    """
    def __init__(self, storage_file: str = "logs/processed_jobs.json"):
        self.file_path = Path(storage_file)
        self.processed_ids: set[str] = set()
        self._lock = asyncio.Lock()
        self._load()

    def _load(self):
        try:
            if self.file_path.exists():
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.processed_ids = set(data)
                        logger.info(f"💾 DedupStore: Loaded {len(self.processed_ids)} processed job IDs from disk.")
            else:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                self._save_sync()
        except Exception as e:
            logger.warning(f"Failed to load processed jobs cache: {e}. Starting fresh.")
            self.processed_ids = set()

    def _save_sync(self):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                # Keep last 10,000 IDs to avoid unbounded file growth
                json.dump(list(self.processed_ids)[-10000:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save processed jobs cache: {e}")

    async def is_processed(self, job_id: str) -> bool:
        async with self._lock:
            return job_id in self.processed_ids

    async def mark_processed(self, job_id: str):
        async with self._lock:
            if job_id not in self.processed_ids:
                self.processed_ids.add(job_id)
                # Persist to disk asynchronously in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._save_sync)

dedup_store = DedupStore()
