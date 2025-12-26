from aiogram import Bot
from config.settings import settings
from core.logger import logger

class Notifier:
    """
    Aiogram bot for sending vacancy alerts.
    """
    def __init__(self):
        self.bot = Bot(token=settings.BOT_TOKEN)

    async def send_vacancy_alert(self, data: dict, link: str):
        """
        Sends formatted markdown notice to the admin.
        """
        score = data.get("score", 0)
        company = data.get("company", "Unknown")
        salary = data.get("salary", "N/A")
        cover_letter = data.get("cover_letter", "")
        red_flags = ", ".join(data.get("red_flags", []))

        message = (
            f"🔥 **Score: {score}/10** | {company}\n"
            f"💰 **Salary:** {salary}\n\n"
            f"⚠️ **Red Flags:** {red_flags if red_flags else 'None'}\n\n"
            f"✍️ **Draft:**\n"
            f"{cover_letter}\n\n"
            f"🔗 [Link to post]({link})"
        )

        try:
            await self.bot.send_message(
                chat_id=settings.ADMIN_ID,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

notifier = Notifier()
