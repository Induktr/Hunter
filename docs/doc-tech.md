# Техническая Документация

### 1. Структура Проекта (Модульный Монолит)

```text
hunter/
├── core/
│   ├── config.py          # Загрузка .env и списков каналов
│   └── logger.py          # Логирование в файл и консоль
├── ears/
│   └── listener.py        # Telethon client, event loop
├── brain/
│   └── gemini_client.py   # Обертка над Google AI SDK
│   └── filters.py         # Regex логика (Hard filter)
├── mouth/
│   └── notifier.py        # Aiogram bot для отправки алертов
├── .env                   # API_ID, API_HASH, BOT_TOKEN, GEMINI_KEY
└── main.py                # Точка входа (Orchestrator)

2. Поток Данных (Data Flow)
Event: Telethon ловит новое сообщение.
Hard Filter: Проверка re.search(stop_words). Если найдено — DROP.
Soft Filter: Проверка re.search(keywords). Если не найдено — DROP.
AI Processing:
Очистка текста (удаление HTML, лишних эмодзи).
Запрос к API Gemini.
Logic Gate: Если ai_response.score < 6 — LOG & DROP.
Notification: Форматирование сообщения и отправка через notifier.py.
3. Конфигурация .env

TG_API_ID=123456
TG_API_HASH=abcdef...
TG_BOT_TOKEN=123:ABC...
GEMINI_API_KEY=AIza...
ADMIN_ID=твоя_телеграм_id

---

### **Файл 4: `docs/DocLogic.md` (Когнитивная Модель)**

```markdown
# Логика "Мозга" (AI Prompt Engineering)

Здесь описано, как мы программируем поведение Gemini.

### 1. Системная Роль (System Instruction)

> **Role:** Ты — Senior HR-аналитик и эксперт по переговорам (стиль Криса Восса). Твоя задача — найти идеальный мэтч для Junior/Middle Frontend разработчика.

### 2. Промпт Анализа (Analysis Prompt)

Входящие данные: Текст вакансии.
Задача ИИ: Вернуть JSON.

**Структура JSON:**
```json
{
  "score": "Оценка 1-10. (10 - идеальный стек React/Next.js, удаленка, хорошая ЗП. 1 - легаси, офис, низкая ЗП)",
  "company": "Название компании",
  "salary": "Вилка или 'Не указано'",
  "key_requirements": ["React", "TS", "Tailwind"],
  "red_flags": ["Стрессоустойчивость", "Печеньки вместо ЗП"],
  "cover_letter": "Текст отклика"
}

3. Методология Генерации Отклика (Voss Style)
При генерации cover_letter ИИ должен следовать правилам:
No "I" statements: Избегать начала предложений с "Я".
Labeling: Использовать фразы "Здається, ви шукаєте..." (It seems like you are looking for...).
Mirorring: Использовать ключевые слова из вакансии.
Calibrated Question: Заканчивать вопросом "Як ми можемо обговорити, чи підходжу я для цієї ролі?".
Язык: Строго на языке вакансии (UA/EN).
