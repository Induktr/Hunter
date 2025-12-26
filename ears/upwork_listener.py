import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from config.settings import settings
from core.logger import logger
from brain.filters import ContentFilter
from brain.ai_client import ai_client
from mouth.notifier import notifier

class UpworkListener:
    """
    Upwork jobs listener with Connects protection.
    Uses direct requests with Session Cookie.
    """
    def __init__(self):
        self.base_url = "https://www.upwork.com/nx/search/jobs/"
        self.dashboard_url = "https://www.upwork.com/nx/find-work/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": settings.UPWORK_COOKIE
        }
        self.processed_ids = set()
        self.current_connects = 999 

    async def start(self):
        if not settings.UPWORK_COOKIE:
            logger.warning("Upwork: No UPWORK_COOKIE found in .env. Upwork monitor disabled.")
            return

        logger.info(f"Starting Upwork listener (Min connects: {settings.UPWORK_MIN_CONNECTS})...")
        
        while True:
            try:
                # 1. Check connects balance first
                await self.check_connects()
                
                if self.current_connects <= settings.UPWORK_MIN_CONNECTS:
                    logger.warning(f"Upwork: STOPPED. Only {self.current_connects} connects left (Limit: {settings.UPWORK_MIN_CONNECTS})")
                    await asyncio.sleep(3600) # Sleep for 1 hour
                    continue

                # 2. Scrape jobs
                for keyword in settings.UPWORK_KEYWORDS:
                    await self.scrape_keyword(keyword)
                    await asyncio.sleep(15) 
                
                logger.info(f"Upwork: Scan completed ({self.current_connects} connects left), sleeping for 20 minutes...")
                await asyncio.sleep(1200) 
                
            except Exception as e:
                logger.error(f"Upwork Scraper Error: {e}")
                await asyncio.sleep(60)

    async def check_connects(self):
        """ Parses connects balance from the find-work dashboard. """
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30, follow_redirects=True) as client:
                resp = await client.get(self.dashboard_url)
                if resp.status_code == 200:
                    # Find connects in HTML using regex or BS4
                    # Pattern: "Connects: 51"
                    match = re.search(r'Connects:\s*(\d+)', resp.text)
                    if match:
                        self.current_connects = int(match.group(1))
                        logger.info(f"Upwork: Current connects balance: {self.current_connects}")
                    else:
                        # Try searching for JSON data in script tags
                        soup = BeautifulSoup(resp.text, "html.parser")
                        # Some versions of Upwork store it in sidebar
                        sidebar = soup.find(id="sidebar-container")
                        if sidebar:
                            c_match = re.search(r'(\d+)\s*Connects', sidebar.text)
                            if c_match:
                                self.current_connects = int(c_match.group(1))
        except Exception as e:
            logger.error(f"Upwork: Failed to check connects: {e}")

    async def scrape_keyword(self, keyword: str):
        # Using search API (simulating browser search)
        params = {
            "q": keyword,
            "sort": "recency",
            "ontology_skill_filter": keyword
        }

        async with httpx.AsyncClient(headers=self.headers, timeout=20) as client:
            response = await client.get(self.base_url, params=params)
            if response.status_code != 200:
                return

            soup = BeautifulSoup(response.text, "html.parser")
            # Upwork standard job card selector
            job_cards = soup.find_all("section", class_="up-card-section")

            for card in job_cards:
                try:
                    title_elem = card.find("h3", class_="job-tile-title")
                    if not title_elem: continue
                    
                    link_elem = title_elem.find("a")
                    link = "https://www.upwork.com" + link_elem["href"]
                    job_id = link_elem["href"].split("_")[1].split("/")[0]
                    
                    if job_id in self.processed_ids:
                        continue
                    
                    self.processed_ids.add(job_id)

                    title = title_elem.text.strip()
                    desc_elem = card.find("span", class_="job-tile-description")
                    description = desc_elem.text.strip() if desc_elem else ""

                    full_text = f"Title: {title}\nDescription: {description}"
                    
                    if ContentFilter.check(full_text):
                        logger.info(f"Upwork: Found JUNIOR job: {title}")
                        analysis = await ai_client.analyze_vacancy(full_text)
                        if analysis and analysis.get("score", 0) >= 7:
                            # Add connects info to alert
                            analysis["salary"] = f"{analysis.get('salary')} | 🔌 Connects: {self.current_connects}"
                            await notifier.send_vacancy_alert(analysis, link)

                except Exception as e:
                    continue

upwork_listener = UpworkListener()
