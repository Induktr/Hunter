import asyncio
from google import genai
from google.genai import types
from src.shared.config.settings import settings
from src.shared.core.logger import logger
from src.brain.tsd_schemas import TSDVacancyAnalysisResult, FastTriageResult
from src.brain.rate_limiter import ai_rate_limiter
from src.brain.key_rotator import gemini_key_pool

class AIClient:
    """
    AI Lead Sniper & Career Closer with 2-Stage Cascading Architecture:
    - Stage 1 (Fast Triage): 40-token express scoring (saves 95% quota on low-tier jobs).
    - Stage 2 (Deep TSD Audit): Exhaustive 19-point First-Principles & Chris Voss Tactical Empathy only for Score >= 7.
    - Multi-Key Load Balancing: Rotates through all available keys in GeminiKeyPool.
    """
    def __init__(self):
        self.model_id = "gemini-3.6-flash"

    async def _fast_triage(self, text: str) -> FastTriageResult | None:
        """
        Stage 1: Blazing fast, low-token qualification (Score 1-10).
        """
        triage_prompt = f"""
        Evaluate this job post for a Developer (React, Next.js, TypeScript, Python, FullStack).
        Give a score from 1 (unrelated, low budget < $1000, casino, unpaid) to 10 (high-ticket $3000+, tech match, B2B SaaS, clear pain).
        Set is_promising = true ONLY if score >= 7.

        Post text:
        {text[:2000]}
        """
        try:
            client = gemini_key_pool.get_client()
            async with ai_rate_limiter:
                response = await client.aio.models.generate_content(
                    model=self.model_id,
                    contents=triage_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=FastTriageResult,
                        temperature=0.1,
                    )
                )
            if response.text:
                return FastTriageResult.model_validate_json(response.text)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.warning(f"⚠️ Rate Limit during Fast Triage: {error_str}")
            else:
                logger.warning(f"Fast Triage error: {e}")
        return None

    async def analyze_vacancy(self, text: str) -> dict | None:
        """
        Two-stage cascading analysis:
        1. Express triage to check if score >= 7 (saves quota).
        2. If promising, run full 8-phase TSD v27.2.2 audit.
        """
        # --- STAGE 1: FAST TRIAGE ---
        triage = await self._fast_triage(text)
        if triage is not None:
            logger.info(f"⚡ [Fast Triage]: {triage.company} | Score: {triage.score}/10 | {triage.quick_verdict}")
            if not triage.is_promising or triage.score < 7:
                # Discard low-tier job without burning heavy TSD quota!
                logger.info(f"🚫 [Quota Saver]: Skipping deep TSD audit for low-score job ({triage.score}/10).")
                return {"score": triage.score, "company": triage.company, "is_promising": False}
        else:
            # If triage had a rate limit or failure, avoid immediate heavy call
            logger.warning("Fast triage could not evaluate. Skipping to avoid quota exhaustion.")
            return None

        # --- STAGE 2: DEEP TSD v27.2.2 AUDIT (Only for Score >= 7) ---
        logger.info("💎 [High-Value Lead Detected]: Launching Full TSD v27.2.2 Cognitive Audit...")
        
        system_instruction = f"""
Ты — Senior Solution Architect, Principal FullStack Engineer и элитный B2B Переговорщик, обученный по методологии ФБР Крисса Восса (Never Split the Difference).
Твоя задача: провести исчерпывающий, многослойный аудит задачи/вакансии по авторской методологии "Сократический Диалог" (TSD v27.2.2) и выдать неотразимый оффер.

Ты ОБЯЗАН ответить на КАЖДЫЙ вопрос из чек-листа в точности по заданным паттернам:

══════════════════════════════════════════════════════════════════════════
ФАЗА 0: АРХИТЕКТУРНЫЙ КОРЕНЬ (Дерево под-концепций)
══════════════════════════════════════════════════════════════════════════
1. Атомарна суть дії: Визначити Root Concept.
2. Розгорнути дерево під-концепцій (Root -> Branch -> Leaf).
3. Виявити тип маніпуляції (1 з 8: Створення, Оптимізація, Інтеграція, Міграція, Рефакторинг, Відлагодження, Безпека, Синхронізація).

══════════════════════════════════════════════════════════════════════════
ФАЗА 1: ДЕКОНСТРУКЦИЯ (Вопросы "ЧТО?") — Все 19 пунктов:
══════════════════════════════════════════════════════════════════════════
1. "Три Ключевых Слова": [Слово 1], [Слово 2], [Слово 3].
2. 'Точка Зрения' (Контекст): С точки зрения Бизнеса? Инженера? Пользователя? Системы?
3. "Золотое Предложение": "По своей сути, [Концепция] — это [что-то], что [делает что-то] для [достижения чего-то]".
4. Что это такое? (Определение): "[Концепция] — это [тип], который [что делает]...".
5. О чем это "говорит"? (Сигнал): "Когда я вижу [Концепция], это говорит мне о том, что [смысл/намерение]...".
6. В чем Цель? (Прагматика): "Практическая цель — [ускорить/упростить/защитить] [конкретный процесс]...".
7. В чем Миссия? (Философия): "Миссия этой технологии — [описание идеологии]...".
8. Какую ОДНУ главную проблему решает эта концепция? (Зачем ее придумали?).
9. Из каких КЛЮЧЕВЫХ частей/терминов состоит? (напр., Call Stack, Web APIs, Queue).
10. Как эти части взаимодействуют друг с другом? (Последовательность, управление).
11. [Синтез действий]: Слово -> Толкование -> Формула смысла.
12. "Intentional vs. Accidental": Что делает специально, а что — побочные/случайные эффекты?
13. "Lifecycle Root": Старт ("Трение") -> Финал ("Твердая Система/SOP").
14. Внешняя сторона (UI/Синтаксис) vs Внутренняя сторона (Логика, память, потоки, биты, IRQ, Hoisting, Heap/Stack).
15. Какие зависимости есть в концепции? (Факторы зависимости).
16. [Visual Audit]: Отрисовать на Whiteboard (Схема: Данные -> Память -> Связи, Stack -> Heap).
17. С чего началась проблема над данной концепцией? (Первопричина трения).
18. [Concept Triad]: Тройная трактовка (Прагматика, Физика/Система, Био-система/Психология).
19. На чём основана данная концепция? (Философия): "[Концепция] основана на [Субстрат], основание всегда идет от [Субстрат]".

══════════════════════════════════════════════════════════════════════════
ФАЗА 2: АНАЛОГИЯ (Вопросы "НА ЧТО ПОХОЖЕ?")
══════════════════════════════════════════════════════════════════════════
1. Объяснение [брату Дане] (простая жизненная аналогия без птичьего языка).
2. Битва конкурентов (A vs B): В чем фундаментальное отличие? Где побеждает А, а где с треском проигрывает Б?

══════════════════════════════════════════════════════════════════════════
ФАЗА 3: КОНТЕКСТ И ПРИМЕНЕНИЕ (Вопросы "ГДЕ и КОГДА?")
══════════════════════════════════════════════════════════════════════════
1. Где в моих проектах (BrainMessenger, Westbud, Квест, Hunter) я уже использовал это?
2. Когда использовать ПРАВИЛЬНО, а когда НЕПРАВИЛЬНО ("Анти-грабли")?
3. Какие "Помощники" (библиотеки, API, инструменты)?
4. 'Принцип 8 Элементов Бизнеса' (Ценность, Маркетинг, Команда, Продукт, Продажи, Финансы, Система Управления, Миссия).
5. Вопрос 'Первого Принципа': ПОЧЕМУ работает именно так? (Компромиссы и исторические причины).
6. [Аудит плюсов и минусов]: Pros, Cons, Ограничения, Сравнительная Битва, Вердикт.
7. 'Creator ROI': Что приносит концепция тебе как Архитектору?

══════════════════════════════════════════════════════════════════════════
ФАЗА 4: МЕТАФОРА ИЗ РЕАЛЬНОГО МИРА
══════════════════════════════════════════════════════════════════════════
1. Метафора (ресторан, машина, стройка, организм): "[Часть системы] — это [часть аналогии]...".

══════════════════════════════════════════════════════════════════════════
ФАЗА 5: КОНТЕКСТ И СТРАТЕГИЯ
══════════════════════════════════════════════════════════════════════════
1. Рычаг: Где даст максимальный leverage?
2. Риски / Анти-грабли.
3. Фильтр Эффективности: "Витамин" или "Болеутоляющее"? Сила рычага 1-10.
4. Фильтр Антихрупкости (Хрупкая vs Антихрупкая).
5. Сценарии: Happy Path, Failure State, Edge Case.
8. Алгоритмическая последовательность (Шаг 1 -> Финал).
9. Жизненный цикл (Подготовка -> Активная фаза -> Валидация -> Очистка).
12. Сферический обзор 360° (Builder, User, Owner, Architecture).
13. Ценностное предложение (Выгода Времени, Денег, Энергии).
15. Аудит надежности (SPOF, Вероятность сбоя 1-10, Последствия, План "Б").

══════════════════════════════════════════════════════════════════════════
ФАЗА 6: СОВЕТЫ МАСТЕРА (Кристаллизация Мудрости)
══════════════════════════════════════════════════════════════════════════
1. Совет по ПРИМЕНЕНИЮ: "Всегда используй [X], когда [Y]".
2. Совет по БЕЗОПАСНОСТИ: "Никогда не используй [X] для [Y], потому что [Z]".
3. Совет по ОПТИМИЗАЦИИ: "Чтобы выжать максимум, всегда [Z]".
4. Сверка с Арифметикой (+, -, *, /): "По своей сути, это просто [операция]...".

══════════════════════════════════════════════════════════════════════════
ФАЗА 7: ОПЕРАТИВНОЕ УПРАВЛЕНИЕ ПЕРЕГОВОРАМИ (Крисс Восс)
══════════════════════════════════════════════════════════════════════════
- Блок 1: Голос Ночного диджея и Mirroring (1-3 слова + пауза).
- Блок 2: Labeling (без "Я") и Accusation Audit (превентивный жесткий аудит обвинений).
- Блок 3: Вопросы на "Как" и "Что" + Стремление к "НЕТ" (No-Oriented Questions).
- Блок 4: Черные лебеди (скрытые страхи) и нейтрализация слова "Справедливость".
- Блок 5: Резюме для "That's Right" (Это верно) и Rule of Three.

══════════════════════════════════════════════════════════════════════════
ФИНАЛЬНЫЙ ПИТЧ (KILLER PITCH):
══════════════════════════════════════════════════════════════════════════
Сформируй лаконичный, бьющий в цель отклик со ссылкой на портфолио ({settings.PORTFOLIO_URL}) и No-Oriented CTA.
"""

        prompt = f"""
        Выполни полный аудит по протоколу TSD v27.2.2 (со всеми 19 пунктами Деконструкции и всеми фазами) для следующего текста вакансии / лида:

        --- ТЕКСТ ВАКАНСИИ / ЗАПРОСА ---
        {text}
        -------------------------------
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
                            response_schema=TSDVacancyAnalysisResult,
                            temperature=0.25,
                        )
                    )

                if not response.text:
                    logger.warning("Empty response from Gemini for TSD v27.2.2 analysis.")
                    return None

                parsed_data = TSDVacancyAnalysisResult.model_validate_json(response.text)
                dumped = parsed_data.model_dump()
                dumped["cover_letter"] = dumped["killer_pitch"]
                
                logger.info(f"🎯 TSD v27.2.2 Full Checklist Audit Completed: {dumped['company']} | Score: {dumped['score']}/10")
                return dumped

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt <= len(delays):
                        wait_time = delays[attempt - 1]
                        logger.warning(f"⚠️ Rate Limit in TSD v27.2.2 analysis. Retry {attempt}/{len(delays)} after {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        attempt += 1
                        continue
                    else:
                        logger.error("❌ Rate limit exhausted during TSD v27.2.2 analysis.")
                else:
                    logger.error(f"❌ Error in TSD v27.2.2 AI analysis: {error_str}")

                return None

ai_client = AIClient()
