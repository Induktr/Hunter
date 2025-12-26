import json
from google import genai
from google.genai import types
from config.settings import settings
from core.logger import logger

class AIClient:
    """
    Logic for Gemini AI analysis and Cover Letter generation using the new google-genai SDK.
    """
    
    def __init__(self):
        # Initializing the client with the API key
        self.client = genai.Client(api_key=settings.GEMINI_KEY)
        self.model_id = "gemini-2.0-flash-lite-preview-02-05"

    async def analyze_vacancy(self, text: str) -> dict | None:
        """
        Analyzes vacancy text and returns structured data using Gemini 2.0 Flash Lite.
        """
        system_instruction = "You are an HR analyst and negotiation expert."
        
        prompt = f"""
        Analyze the following job vacancy.
        
        Task:
        1. Evaluate the vacancy (score 1-10) based on relevance and quality.
        2. Write a Cover Letter using Chris Voss methodology (Labeling: "Здається, ви шукаєте...", Calibrated Question at the end).
        3. Identify any red flags.
        
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
