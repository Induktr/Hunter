import json
from google import genai
from google.genai import types
from src.shared.config.settings import settings
from src.shared.core.logger import logger

class AIClient:
    """
    Logic for Gemini AI analysis and Cover Letter generation using the new google-genai SDK.
    """
    
    def __init__(self):
        # Initializing the client with the API key
        self.client = genai.Client(api_key=settings.GEMINI_KEY)
        self.model_id = "gemini-3-flash-preview"

    async def analyze_vacancy(self, text: str) -> dict | None:
        """
        Analyzes vacancy text and returns structured data using Gemini 2.0 Flash Lite.
        Focuses on JUNIOR positions and MARKETING the user's portfolio.
        """
        system_instruction = (
            "You are an active Career Agent for a Junior Frontend Developer. "
            "Your Goal: Convert job views into Portfolio clicks."
        )
        
        prompt = f"""
        Analyze the following job vacancy for a JUNIOR developer.
        
        Task:
        1. Evaluate the vacancy (score 1-10).
        2. Write a "Killer" Cover Letter that SELLS the candidate.
           - CRITICAL: You MUST include this portfolio link: {settings.PORTFOLIO_URL}
           - CONTEXT: Don't just paste the link. Say something like: "I recently implemented a similar [Technology from job desc] feature in my portfolio: {settings.PORTFOLIO_URL}"
           - TONE: Confident, hungry to learn, professional.
           - ENDING: Use a Call to Action (CTA) asking them to visit the site.
        3. Identify red flags.
        
        Output MUST be a STRICT JSON object:
        {{
            "score": int,
            "company": str,
            "salary": str,
            "cover_letter": str,
            "red_flags": list
        }}
        
        Vacancy Text:
        {text}
        """

        try:
            # Using the new SDK's generation method
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json"
                )
            )
            
            # Since generate_content in the new SDK is synchronous by default in common usage,
            # but usually implemented via thread pool or actually blocking, 
            # we should use a proper async approach if available or just handle it.
            # google-genai has an async client too: genai.Client(..., http_options={'api_version': 'v1beta'})
            
            data = json.loads(response.text)
            return data
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return None

ai_client = AIClient()
