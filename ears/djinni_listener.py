import asyncio
import httpx
from bs4 import BeautifulSoup
from config.settings import settings
from core.logger import logger
from brain.filters import ContentFilter
from brain.ai_client import ai_client
from mouth.notifier import notifier

class DjinniListener:
    """
    Scraper for Djinni.co jobs using direct HTTP requests.
    """
    def __init__(self):
        self.base_url = "https://djinni.co/jobs/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        self.processed_ids = set()

    async def start(self):
        logger.info(f"Starting Djinni listener for: {settings.DJINNI_KEYWORDS}")
        
        while True:
            try:
                for keyword in settings.DJINNI_KEYWORDS:
                    await self.scrape_keyword(keyword)
                    await asyncio.sleep(10) # Antispam delay
                
                logger.info("Djinni: Scan completed, sleeping for 20 minutes...")
                await asyncio.sleep(1200) 
                
            except Exception as e:
                logger.error(f"Djinni Scraper Error: {e}")
                await asyncio.sleep(60)

    async def scrape_keyword(self, keyword: str):
        # We check both "no_exp" and "1y" for Juniors
        for exp in ["no_exp", "1y"]:
            params = {
                "primary_keyword": keyword,
                "exp_level": exp,
                "sort": "date"
            }

            async with httpx.AsyncClient(headers=self.headers, timeout=20) as client:
                response = await client.get(self.base_url, params=params)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                # Djinni structure: list-jobs__item contains the link
                job_items = soup.find_all("li", class_="list-jobs__item")

                for item in job_items:
                    try:
                        title_elem = item.find("a", class_="job-list-item__link")
                        if not title_elem: continue
                        
                        link = "https://djinni.co" + title_elem["href"]
                        job_id = title_elem["href"].split("/")[2].split("-")[0] # Simple ID extraction
                        
                        if job_id in self.processed_ids:
                            continue
                        
                        self.processed_ids.add(job_id)

                        title = title_elem.text.strip()
                        description = item.find("div", class_="job-list-item__description")
                        desc_text = description.text.strip() if description else ""
                        
                        full_text = f"Title: {title}\nDescription: {desc_text}"
                        
                        # 1. Filter
                        if ContentFilter.check(full_text):
                            logger.info(f"Djinni: Found JUNIOR job: {title}")
                            # 2. AI Analysis & Notify

                        # 2. AI Analysis & Notify
                        analysis = await ai_client.analyze_vacancy(full_text)
                        if analysis and analysis.get("score", 0) >= 7:
                            logger.info(f"Djinni Job score {analysis['score']} >= 7. Notifying...")
                            await notifier.send_vacancy_alert(analysis, link)

                    except Exception as e:
                        logger.debug(f"Error parsing Djinni item: {e}")
                        continue

djinni_listener = DjinniListener()
