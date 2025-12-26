import asyncio
from brain.ai_client import ai_client
from mouth.notifier import notifier
from core.logger import logger

async def test_pipeline():
    """
    Temporary script to test the full logic: AI analysis + Telegram notification.
    """
    test_vacancy = """
    Ищем Middle React Developer в инновационный стартап!
    Стек: React, TypeScript, Next.js, Redux.
    Мы предлагаем:
    - Зарплата $4000 - $6000
    - Полная удаленка
    - Опционы компании
    - ДМС и курсы английского
    Контакт: @hr_manager_test
    """
    
    logger.info("🧪 Запуск теста пайплайна...")
    
    # 1. Симулируем прохождение фильтров (пропускаем их для теста)
    logger.info("1. Анализируем вакансию через Gemini...")
    
    analysis = await ai_client.analyze_vacancy(test_vacancy)
    
    if not analysis:
        logger.error("❌ Ошибка: ИИ не вернул результат.")
        return

    logger.info(f"2. ИИ вернул результат! Score: {analysis.get('score')}")
    
    # 3. Отправляем уведомление
    logger.info("3. Передаем данные в Notifier...")
    await notifier.send_vacancy_alert(analysis, "https://t.me/test_channel/123")
    
    logger.info("✅ Тест завершен! Проверьте своего бота в Telegram.")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
