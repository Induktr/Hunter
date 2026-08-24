import asyncio
import httpx
from bs4 import BeautifulSoup
from src.shared.config.settings import settings
from src.shared.core.logger import logger
from src.features.brain.filters import ContentFilter
from src.shared.api.ai_client import ai_client
from src.features.mouth.notifier import notifier
from src.shared.utils.dedup_store import dedup_store

class LinkedinListener:
    """
    Lightweight LinkedIn scraper with persistent disk deduplication and rate-controlled card parsing.
    """
    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def start(self):
        logger.info("Starting lightweight LinkedIn listener (with DedupStore)...")
        
        while True:
            try:
                for keyword in settings.LINKEDIN_KEYWORDS:
                    await self.scrape_keyword(keyword)
                    await asyncio.sleep(10) # Delay between keywords
                
                logger.info("⏳ LinkedIn: Scan completed. Next check in 15 minutes...")
                await asyncio.sleep(900) 
                
            except Exception as e:
                logger.error(f"LinkedIn Scraper Error: {e}")
                await asyncio.sleep(60)

    async def scrape_keyword(self, keyword: str):
        params = {
            "keywords": keyword,
            "location": settings.LINKEDIN_LOCATION,
            "f_TPR": "r86400", # Past 24 hours
            "start": 0
        }

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=20) as client:
                response = await client.get(self.base_url, params=params)
                if response.status_code != 200:
                    logger.warning(f"LinkedIn returned status {response.status_code} for {keyword}")
                    return

                soup = BeautifulSoup(response.text, "html.parser")
                job_cards = soup.find_all("li")

                for card in job_cards:
                    try:
                        job_id_element = card.find("div", {"data-entity-urn": True})
                        if not job_id_element: continue
                        
                        raw_id = job_id_element["data-entity-urn"].split(":")[-1]
                        job_id = f"linkedin_{raw_id}"
                        
                        # Persistent Deduplication Check (Saves quota across runs)
                        if await dedup_store.is_processed(job_id):
                            continue
                        
                        await dedup_store.mark_processed(job_id)

                        title_elem = card.find("h3", class_="base-search-card__title")
                        company_elem = card.find("h4", class_="base-search-card__subtitle")
                        link_elem = card.find("a", class_="base-card__full-link")
                        
                        if not title_elem or not link_elem: continue

                        title = title_elem.text.strip()
                        company = company_elem.text.strip() if company_elem else "Unknown"
                        link = link_elem["href"].split("?")[0]

                        text_to_check = f"{title} {company}"
                        
                        if ContentFilter.check(text_to_check):
                            logger.info(f"LinkedIn: Found candidate job: {title} at {company}")
                            
                            description = await self.fetch_job_description(client, link)
                            full_text = f"Title: {title}\nCompany: {company}\n\nDescription:\n{description}"
                            
                            # 2-Stage Analysis (Fast Triage -> Deep TSD)
                            analysis = await ai_client.analyze_vacancy(full_text)
                            if analysis and analysis.get("score", 0) >= 7:
                                logger.info(f"🎯 LinkedIn High-Value job ({analysis.get('score')}/10). Sending alert...")
                                await notifier.send_vacancy_alert(analysis, link)

                            # Pacing delay between processing cards to prevent API bursts
                            await asyncio.sleep(2)

                    except Exception as e:
                        logger.debug(f"Error parsing LinkedIn job card: {e}")
                        continue
        except Exception as e:
            logger.warning(f"LinkedIn network error for {keyword}: {e}")

    async def fetch_job_description(self, client: httpx.AsyncClient, url: str) -> str:
        try:
            resp = await client.get(url, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                desc = soup.find("div", class_="description__text")
                return desc.get_text(separator="\n").strip() if desc else "No description found"
        except:
            return ""
        return ""

linkedin_listener = LinkedinListener()
