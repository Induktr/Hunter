import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from src.shared.config.settings import settings
from src.shared.core.logger import logger
from src.features.brain.filters import ContentFilter
from src.shared.api.ai_client import ai_client
from src.features.mouth.notifier import notifier
from src.shared.utils.dedup_store import dedup_store

class UpworkListener:
    """
    Upwork jobs listener with persistent disk-backed deduplication and adaptive polling.
    """
    def __init__(self):
        self.base_url = "https://www.upwork.com/nx/search/jobs/"
        self.dashboard_url = "https://www.upwork.com/nx/find-work/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": settings.UPWORK_COOKIE
        }
        self.current_connects = 999 

    async def start(self):
        if not settings.UPWORK_COOKIE:
            logger.info("Upwork: UPWORK_COOKIE is not configured. Upwork monitor sleeping...")
            while not settings.UPWORK_COOKIE:
                await asyncio.sleep(3600)

        logger.info(f"Starting Upwork listener (Min connects: {settings.UPWORK_MIN_CONNECTS})...")
        
        while True:
            try:
                # 1. Check connects balance first
                await self.check_connects()
                
                if self.current_connects <= settings.UPWORK_MIN_CONNECTS:
                    logger.warning(f"Upwork: STOPPED. Only {self.current_connects} connects left (Limit: {settings.UPWORK_MIN_CONNECTS})")
                    await asyncio.sleep(3600)
                    continue

                # 2. Scrape jobs with persistent deduplication
                for keyword in settings.UPWORK_KEYWORDS:
                    await self.scrape_keyword(keyword)
                    await asyncio.sleep(10)
                
                logger.info(f"⏳ Upwork: Scan completed ({self.current_connects} connects left). Next check in 15 minutes...")
                await asyncio.sleep(900)
                
            except Exception as e:
                logger.error(f"Upwork Scraper Error: {e}")
                await asyncio.sleep(60)

    async def check_connects(self):
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30, follow_redirects=True) as client:
                resp = await client.get(self.dashboard_url)
                if resp.status_code == 200:
                    match = re.search(r'Connects:\s*(\d+)', resp.text)
                    if match:
                        self.current_connects = int(match.group(1))
                        logger.info(f"Upwork: Current connects balance: {self.current_connects}")
        except Exception as e:
            logger.debug(f"Upwork: Failed to check connects: {e}")

    async def scrape_keyword(self, keyword: str):
        params = {
            "q": keyword,
            "sort": "recency",
            "ontology_skill_filter": keyword
        }

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=20) as client:
                response = await client.get(self.base_url, params=params)
                
                if response.status_code != 200:
                    logger.warning(f"Upwork: Request failed for {keyword} with status {response.status_code}. Check Cookie!")
                    return

                soup = BeautifulSoup(response.text, "html.parser")
                job_cards = soup.find_all("section", class_="up-card-section")

                for card in job_cards:
                    try:
                        title_elem = card.find("h3", class_="job-tile-title")
                        if not title_elem: continue
                        
                        link_elem = title_elem.find("a")
                        link = "https://www.upwork.com" + link_elem["href"]
                        raw_id = link_elem["href"].split("_")[1].split("/")[0]
                        job_id = f"upwork_{raw_id}"
                        
                        # Persistent Deduplication Check
                        if await dedup_store.is_processed(job_id):
                            continue
                        
                        await dedup_store.mark_processed(job_id)

                        title = title_elem.text.strip()
                        desc_elem = card.find("span", class_="job-tile-description")
                        description = desc_elem.text.strip() if desc_elem else ""

                        full_text = f"Title: {title}\nDescription: {description}"
                        
                        if ContentFilter.check(full_text):
                            logger.info(f"Upwork: Analyzing new candidate job: {title}")
                            analysis = await ai_client.analyze_vacancy(full_text)
                            if analysis and analysis.get("score", 0) >= 7:
                                analysis["salary"] = f"{analysis.get('salary')} | 🔌 Connects: {self.current_connects}"
                                await notifier.send_vacancy_alert(analysis, link)

                    except Exception as e:
                        continue
        except Exception as e:
            logger.warning(f"Upwork network error: {e}")

upwork_listener = UpworkListener()
