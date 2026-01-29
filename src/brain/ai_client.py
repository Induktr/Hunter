import json
import asyncio
from google import genai
from google.genai import types
from src.shared.config.settings import settings
from src.shared.core.logger import logger

class AIResearcher:
    """
    Enhanced AI Client for general research tasks.
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_KEY)
        self.model_id = "gemini-2.0-flash" 

    async def perform_research(self, topic: str, search_results: str) -> list:
        """
        Analyzes web search results and returns a structured list for Excel export.
        Includes a retry mechanism for API rate limits.
        """
        system_instruction = (
            "You are a Senior Research Analyst. Your task is to extract high-quality, "
            "structured data from web search results."
        )
        
        prompt = f"""
        Analyze the following web search results about: "{topic}"
        
        Task:
        1. Identify the top 10 relevant objects, companies, or products.
        2. Extract details according to these columns: [Name, Location, Key Specs, Price/Value, Link].
        3. Format the output as a STRICT JSON array of objects.
        
        Output Format example:
        [
            {{
                "Name": "Example Corp",
                "Location": "San Francisco, CA",
                "Key Specs": "AI Automation, SaaS, 50-100 employees",
                "Price/Value": "$5,000 - $20,000",
                "Link": "https://example.com"
            }}
        ]
        
        Search Results Content:
        {search_results}
        
        STRICT JSON ARRAY OUTPUT ONLY:
        """

        delays = [10, 20, 30]
        attempt = 1

        while True:
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json"
                    )
                )
                
                data = json.loads(response.text)
                if isinstance(data, list):
                    return data
                return []

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt <= len(delays):
                        wait_time = delays[attempt - 1]
                        logger.warning(f"🤖 AI is tired (Rate Limit). Attempt {attempt}/4 failed. Resting for {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        attempt += 1
                        continue
                    else:
                        logger.error("❌ AI Research Failed: The API is overloaded and all retry attempts were exhausted. Please try again in a few minutes.")
                else:
                    logger.error(f"❌ AI Research Error: {error_str}")
                
                return []

ai_researcher = AIResearcher()
