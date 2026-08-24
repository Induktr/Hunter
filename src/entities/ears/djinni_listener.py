import asyncio
import httpx
from bs4 import BeautifulSoup
from src.shared.config.settings import settings
from src.shared.core.logger import logger
from src.features.brain.filters import ContentFilter
from src.shared.api.ai_client import ai_client
from src.features.mouth.notifier import notifier
from src.shared.utils.dedup_store import dedup_store

class DjinniListener:
    """
    Scraper for Djinni.co jobs with persistent disk-backed deduplication and adaptive polling.
    """
    def __init__(self):
        self.base_url = "https://djinni.co/jobs/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    async def start(self):
        logger.info(f"Starting Djinni listener for: {settings.DJINNI_KEYWORDS}")
        
        while True:
            try:
                for keyword in settings.DJINNI_KEYWORDS:
                    await self.scrape_keyword(keyword)
                    await asyncio.sleep(5) # Gentle antispam delay
                
                logger.info("⏳ Djinni: Scan completed. Next adaptive check in 15 minutes...")
                await asyncio.sleep(900) # 15 minutes adaptive cycle
                
            except Exception as e:
                logger.error(f"Djinni Scraper Error: {e}")
                await asyncio.sleep(60)

    async def scrape_keyword(self, keyword: str):
        for exp in ["no_exp", "1y"]:
            params = {
                "primary_keyword": keyword,
                "exp_level": exp,
                "sort": "date"
            }

            try:
                async with httpx.AsyncClient(headers=self.headers, timeout=20) as client:
                    response = await client.get(self.base_url, params=params)
                    
                    if response.status_code != 200:
                        logger.warning(f"Djinni: Request failed for {keyword} with status {response.status_code}")
                        continue

                    soup = BeautifulSoup(response.text, "html.parser")
                    job_links = soup.find_all("a", href=lambda href: href and "/jobs/" in href and href.split("/jobs/")[1][:1].isdigit())

                    for link_elem in job_links:
                        try:
                            href = link_elem["href"]
                            if "reviews" in href: continue

                            job_id = f"djinni_{href.split('/')[2].split('-')[0]}"
                            
                            # Persistent Deduplication Check (Saves 60% quota)
                            if await dedup_store.is_processed(job_id):
                                continue
                            
                            await dedup_store.mark_processed(job_id)

                            title = link_elem.text.strip()
                            if not title: continue

                            full_link = "https://djinni.co" + href
                            container = link_elem.find_parent("div", class_=lambda c: c and "job" in c)
                            if not container:
                                container = link_elem.find_parent("li") or link_elem.find_parent("div")
                            
                            desc_text = container.get_text(separator="\n").strip() if container else title
                            full_text = f"Title: {title}\nDescription: {desc_text}"
                            
                            # Fast content filter check
                            if ContentFilter.check(full_text):
                                logger.info(f"Djinni: Analyzing new candidate job: {title}")
                                analysis = await ai_client.analyze_vacancy(full_text)
                                if analysis and analysis.get("score", 0) >= 7:
                                    logger.info(f"🎯 Djinni Job score {analysis['score']} >= 7. Notifying...")
                                    await notifier.send_vacancy_alert(analysis, full_link)

                        except Exception as e:
                            logger.debug(f"Error parsing Djinni item: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Djinni network error for {keyword}: {e}")

djinni_listener = DjinniListener()
