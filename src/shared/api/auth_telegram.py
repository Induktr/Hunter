import asyncio
import os
from pathlib import Path
from telethon import TelegramClient
from src.shared.config.settings import settings

async def main():
    print("\n🔐 --- ИНТЕРАКТИВНАЯ АВТОРИЗАЦИЯ TELEGRAM (TELETHON) ---")
    session_file = Path("hunter_session.session")
    
    if session_file.exists():
        print(f"🗑️ Удаляем устаревший недействительный файл: {session_file}...")
        try:
            os.remove(session_file)
            print("✅ Старый файл сессии успешно удален.")
        except Exception as e:
            print(f"⚠️ Не удалось удалить файл: {e}")

    print("\n📱 Сейчас Telethon запросит ваш номер телефона и код из Telegram.")
    print("Вводите номер в международном формате (например, +380... или +7...):")
    
    client = TelegramClient('hunter_session', settings.API_ID, settings.API_HASH)
    
    await client.start()
    
    me = await client.get_me()
    print(f"\n🎉 УСПЕШНАЯ АВТОРИЗАЦИЯ! Вы вошли как: {me.first_name} (@{me.username})")
    print("Файл 'hunter_session.session' успешно создан и привязан к вашему текущему IP.\n")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
