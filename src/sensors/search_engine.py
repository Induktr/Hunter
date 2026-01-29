from tavily import TavilyClient
from src.shared.config.settings import settings
from src.shared.core.logger import logger

class SearchEngine:
    def __init__(self):
        if not settings.TAVILY_API_KEY:
            logger.warning("TAVILY_API_KEY not found in settings. Search functionality will be limited.")
        self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    async def search(self, query: str) -> dict:
        """
        Performs a web search using Tavily API.
        Returns a dictionary with clean text content and a list of source URLs.
        """
        logger.info(f"Researching: {query}")
        try:
            # Using search with include_answer and include_raw_content for better context
            response = self.client.search(query=query, search_depth="advanced", max_results=5)
            
            clean_text = ""
            sources = []

            for result in response.get('results', []):
                clean_text += f"\n--- Source: {result.get('url')} ---\n"
                clean_text += result.get('content', '') + "\n"
                sources.append(result.get('url'))

            return {
                "content": clean_text,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return {"content": "", "sources": []}

search_engine = SearchEngine()
