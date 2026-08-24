import asyncio
from google import genai
from google.genai import types
from src.shared.config.settings import settings
from src.shared.core.logger import logger
from src.brain.schemas import LeadResearchResult
from src.brain.rate_limiter import ai_rate_limiter
from src.brain.key_rotator import gemini_key_pool

class AIResearcher:
    """
    Analyzes web search results and extracts structured, high-value B2B leads
    thoroughly audited through the TSD (Socratic Dialogue Protocol v27.2.2) methodology.
    """
    def __init__(self):
        self.model_id = "gemini-3.6-flash"

    async def perform_research(self, topic: str, search_results: str) -> list[dict]:
        """
        Analyzes search results and returns a structured list of leads ready for Excel export.
        Employs TSD v27.2.2 (Root Concept, Friction Diagnosis, SPOF, and Outreach Hook).
        """
        system_instruction = (
            "Ты — Senior Solution Architect и Lead Generation Specialist, мыслящий по методологии TSD v27.2.2. "
            "Твоя задача: проанализировать поисковую выдачу и вытащить список из топ-10 целевых компаний/лидов, "
            "проведя по каждой из них экспресс-аудит (Root Concept, Диагноз боли 'Болеутоляющее/Витамин', SPOF и Крючок первого касания)."
        )

        prompt = f"""
        Выполни структурированный TSD-анализ поисковой выдачи по теме: "{topic}"

        Задачи:
        1. Выдели до 10 наиболее перспективных компаний, продуктов или потенциальных клиентов.
        2. Для каждого объекта заполни:
           - Name: Название компании
           - Location: Локация (или 'Remote')
           - Root Concept & Tech: Корневой технологический концепт и стек (Фаза 0: Root -> Branch -> Leaf)
           - Pain Type & Friction: Диагноз боли ('БОЛЕУТОЛЯЮЩЕЕ' или 'ВИТАМИН') и скрытое трение бизнеса (Фазы 1-3)
           - Price/Value: Оценка бюджета, финансирования или прайсинга (напр. '$5k-$20k', 'Series A', 'N/A')
           - SPOF & Risk Diagnosis: Выявленная точка отказа / узкое место и направление для решения (Фаза 5)
           - Outreach Pitch Hook: Психологический крючок для первого сообщения с No-Oriented вопросом (Фазы 6-7 Крисса Восса)
           - Link: Официальный рабочий URL сайта / профиля

        Результаты поиска:
        {search_results}
        """

        delays = [5, 15, 30]
        attempt = 1

        while True:
            try:
                client = gemini_key_pool.get_client()
                async with ai_rate_limiter:
                    response = await client.aio.models.generate_content(
                        model=self.model_id,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=LeadResearchResult,
                            temperature=0.2,
                        )
                    )

                if not response.text:
                    logger.warning("Empty response received from Gemini for research.")
                    return []

                parsed_result = LeadResearchResult.model_validate_json(response.text)
                
                # Convert to dictionaries matching expected Excel columns
                records = [item.model_dump(by_alias=True) for item in parsed_result.leads]
                
                logger.info(f"✅ TSD AI Research extracted {len(records)} qualified leads for topic: '{topic}'")
                return records

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt <= len(delays):
                        wait_time = delays[attempt - 1]
                        logger.warning(f"⚠️ Gemini Rate Limit reached in research. Retry {attempt}/{len(delays)} after {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        attempt += 1
                        continue
                    else:
                        logger.error("❌ Gemini Rate Limit exhausted after all retries in research.")
                else:
                    logger.error(f"❌ AI Research Error: {error_str}")

                return []

ai_researcher = AIResearcher()
