import asyncio
import httpx
from bs4 import BeautifulSoup
from config.settings import settings
from core.logger import logger
from brain.filters import ContentFilter
from brain.ai_client import ai_client
from mouth.notifier import notifier

class LinkedinListener:
    """
    Lightweight LinkedIn scraper using direct HTTP requests.
    No browser/Playwright required.
    """
    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.processed_ids = set()

    async def start(self):
        logger.info(f"Starting lightweight LinkedIn listener (HTTP only)...")
        
        while True:
            try:
                for keyword in settings.LINKEDIN_KEYWORDS:
                    await self.scrape_keyword(keyword)
                    await asyncio.sleep(5) # Delay between keywords
                
                # Wait before next full scan
                logger.info("LinkedIn: Scan completed, sleeping for 15 minutes...")
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

        async with httpx.AsyncClient(headers=self.headers, timeout=20) as client:
            response = await client.get(self.base_url, params=params)
            if response.status_code != 200:
                logger.error(f"LinkedIn returned status {response.status_code} for {keyword}")
                return

            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("li")

            for card in job_cards:
                try:
                    job_id_element = card.find("div", {"data-entity-urn": True})
                    if not job_id_element: continue
                    
                    job_id = job_id_element["data-entity-urn"].split(":")[-1]
                    
                    if job_id in self.processed_ids:
                        continue
                    
                    self.processed_ids.add(job_id)

                    title = card.find("h3", class_="base-search-card__title").text.strip()
                    company = card.find("h4", class_="base-search-card__subtitle").text.strip()
                    link = card.find("a", class_="base-card__full-link")["href"].split("?")[0]

                    # For deeper analysis we would need to fetch job description, 
                    # but for speed we can first check the title and company
                    text_to_check = f"{title} {company}"
                    
                    if ContentFilter.check(text_to_check):
                        logger.info(f"LinkedIn: Found JUNIOR job: {title} at {company}")
                        # Fetch full description if title passed filter
                        # Fetch full description if title passed filter
                        description = await self.fetch_job_description(client, link)
                        full_text = f"{title} at {company}\n\n{description}"
                        
                        analysis = await ai_client.analyze_vacancy(full_text)
                        if analysis and analysis.get("score", 0) >= 7:
                            await notifier.send_vacancy_alert(analysis, link)

                except Exception as e:
                    logger.debug(f"Error parsing job card: {e}")
                    continue

    async def fetch_job_description(self, client: httpx.AsyncClient, url: str) -> str:
        """ Fetches the full job description text. """
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                desc = soup.find("div", class_="description__text")
                return desc.get_text(separator="\n").strip() if desc else "No description found"
        except:
            return "Failed to fetch description"
        return ""

linkedin_listener = LinkedinListener()
