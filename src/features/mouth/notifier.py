import html
from aiogram import Bot
from src.shared.config.settings import settings
from src.shared.core.logger import logger

def esc(text: str) -> str:
    """ Escapes special HTML characters for reliable Telegram rendering. """
    return html.escape(str(text or ""))

class Notifier:
    """
    Aiogram bot for sending vacancy alerts with rich, structured TSD v27.2.2 cards.
    Uses HTML parse mode for 100% reliable rendering without entity parsing errors.
    """
    def __init__(self):
        self.bot = Bot(token=settings.BOT_TOKEN)

    async def send_vacancy_alert(self, data: dict, link: str):
        """
        Sends perfectly structured HTML notice with all TSD Diagnostic details (Phases 0-7) to the admin.
        """
        score = data.get("score", 0)
        company = esc(data.get("company", "Unknown"))
        salary = esc(data.get("salary", "N/A"))
        killer_pitch = esc(data.get("killer_pitch") or data.get("cover_letter", ""))
        red_flags = [esc(rf) for rf in data.get("red_flags", [])]
        tsd = data.get("tsd_passport")

        message_parts = [
            f"🎯 <b>Score: {score}/10 | {company}</b>",
            f"💰 <b>Salary/Budget:</b> {salary}",
            "═" * 32
        ]

        # Full Rich TSD v27.2.2 Diagnostic Passport (matching exact schema fields)
        if tsd:
            p0 = tsd.get("phase0_root", {})
            p1 = tsd.get("phase1_deconstruction", {})
            p2 = tsd.get("phase2_analogy", {})
            p3 = tsd.get("phase3_context_application", {})
            p5 = tsd.get("phase5_strategy", {})
            p6 = tsd.get("phase6_wisdom", {})
            p7 = tsd.get("phase7_negotiation", {})

            root_concept = esc(p0.get("root_concept", "N/A"))
            manipulation = esc(p0.get("manipulation_type", ""))
            concept_tree = " ➔ ".join([esc(x) for x in p0.get("concept_tree", [])])
            
            golden_sentence = esc(p1.get("q3_golden_sentence", "N/A"))
            substrate = esc(p1.get("q19_foundational_substrate", "N/A"))
            
            eli5 = esc(p2.get("q1_eli5_brother_danya", "N/A"))
            competitor_battle = esc(p2.get("q2_competitor_battle", "N/A"))
            
            pain_type = esc(p5.get("q3_efficiency_filter", "N/A"))
            spof = esc(p5.get("q15_reliability_spof_audit", "N/A"))
            
            anti_pattern = esc(p6.get("rule_anti_pattern", "N/A"))
            arithmetic = esc(p6.get("arithmetic_axiom", "N/A"))
            
            black_swan = esc(p7.get("block4_black_swans", "N/A"))
            accusation = esc(p7.get("block2_labeling_accusation_audit", "N/A"))
            no_cta = esc(p7.get("no_oriented_cta", "N/A"))

            message_parts.extend([
                f"🧠 <b>[Phase 0 Root]:</b> <code>{root_concept}</code> ({manipulation})",
                f"🌲 <b>[Concept Tree]:</b> {concept_tree}",
                f"🏛️ <b>[Phase 1 Субстрат]:</b> {substrate}",
                f"✨ <b>[Phase 1 Золотое Предложение]:</b> <i>{golden_sentence}</i>",
                f"💥 <b>[Phase 5 Диагноз Боли]:</b> <b>{pain_type}</b>",
                f"🛡️ <b>[Phase 5 SPOF & План Б]:</b> {spof}",
                f"👶 <b>[Phase 2 Аналогия Дане]:</b> <i>{eli5}</i>",
                f"⚔️ <b>[Phase 2 Битва A vs B]:</b> {competitor_battle}",
                f"🦢 <b>[Phase 7 Черный Лебедь]:</b> {black_swan}",
                f"🤝 <b>[Phase 7 Аудит Обвинений]:</b> {accusation}",
                f"❓ <b>[Phase 7 No-Oriented CTA]:</b> {no_cta}",
                f"⚠️ <b>[Phase 6 Anti-Pattern]:</b> {anti_pattern}",
                f"➕ <b>[Phase 6 Арифметика]:</b> {arithmetic}",
                "═" * 32
            ])

        if red_flags:
            message_parts.append(f"🚩 <b>Red Flags:</b> {', '.join(red_flags)}\n")

        message_parts.extend([
            "✍️ <b>[KILLER PITCH (Phase 7)]:</b>",
            f"<i>{killer_pitch}</i>",
            "",
            f"🔗 <a href='{link}'><b>Открыть вакансию / пост</b></a>"
        ])

        message = "\n".join(message_parts)

        try:
            await self.bot.send_message(
                chat_id=settings.ADMIN_ID,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            logger.info(f"✅ Telegram alert sent successfully (HTML mode) for {company}")
        except Exception as e:
            logger.error(f"❌ Error sending Telegram HTML alert: {e}")
            try:
                clean_text = message.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "").replace("<i>", "").replace("</i>", "")
                await self.bot.send_message(
                    chat_id=settings.ADMIN_ID,
                    text=clean_text
                )
            except Exception as e2:
                logger.error(f"Critical error sending message: {e2}")

    async def send_research_report(self, filepath: str, topic: str):
        """
        Sends the generated Excel research report to the admin.
        """
        from aiogram.types import FSInputFile
        
        try:
            document = FSInputFile(filepath)
            await self.bot.send_document(
                chat_id=settings.ADMIN_ID,
                document=document,
                caption=f"✅ Research completed: {esc(topic)}",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send research report: {e}")

notifier = Notifier()
