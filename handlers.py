import asyncio

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from google import genai

from config import settings

router = Router()
client = genai.Client(api_key=settings.gemini_api_key)

TELEGRAM_MESSAGE_LIMIT = 4096
SAFE_MESSAGE_LIMIT = 3900

SYSTEM_PROMPT = """
Ты — мудрый эксперт по китайской метафизике: Ба Цзы, Фэншуй и И Цзин.

Стиль общения:
- отвечай спокойно, уважительно и структурированно;
- избегай фатализма, запугивания и абсолютных предсказаний;
- объясняй, что метафизика — это инструмент анализа, а не приговор;
- давай практичные рекомендации;
- если пользователь спрашивает про Ба Цзы, обязательно запроси дату рождения,
  точное время рождения, город рождения и пол;
- если данных мало, задай уточняющие вопросы;
- не давай медицинских, юридических или финансовых гарантий.
"""

user_contexts: dict[int, list[dict[str, str]]] = {}


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔮 Задать вопрос Ба Цзы")],
            [KeyboardButton(text="🏡 Совет по Фэншуй")],
            [KeyboardButton(text="📜 Книга Перемен (И Цзин)")],
        ],
        resize_keyboard=True,
    )


def get_user_history(user_id: int) -> list[dict[str, str]]:
    if user_id not in user_contexts:
        user_contexts[user_id] = []
    return user_contexts[user_id]


def split_text(text: str, max_length: int = SAFE_MESSAGE_LIMIT) -> list[str]:
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    current = ""

    for paragraph in text.split("\n\n"):
        if len(paragraph) > max_length:
            words = paragraph.split(" ")
            for word in words:
                if len(current) + len(word) + 1 > max_length:
                    if current.strip():
                        chunks.append(current.strip())
                    current = word
                else:
                    current = f"{current} {word}".strip()
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) > max_length:
            if current.strip():
                chunks.append(current.strip())
            current = paragraph
        else:
            current = candidate

    if current.strip():
        chunks.append(current.strip())

    return chunks


async def send_long_message(message: Message, text: str) -> None:
    chunks = split_text(text)
    total = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        prefix = f"Часть {index}/{total}\n\n" if total > 1 else ""
        await message.answer(prefix + chunk)


def build_prompt(history: list[dict[str, str]], user_text: str) -> str:
    recent_history = history[-10:]
    parts = [SYSTEM_PROMPT.strip(), "\nИстория диалога:"]

    for item in recent_history:
        role = "Пользователь" if item["role"] == "user" else "Ассистент"
        parts.append(f"{role}: {item['content']}")

    parts.append(f"Пользователь: {user_text}")
    parts.append("Ассистент:")

    return "\n".join(parts)


def ask_gemini_sync(prompt: str) -> str:
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
    )
    return response.text or "Не удалось получить ответ от Gemini."


async def ask_gemini(user_id: int, user_text: str) -> str:
    history = get_user_history(user_id)
    prompt = build_prompt(history, user_text)

    answer = await asyncio.to_thread(ask_gemini_sync, prompt)

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": answer})

    return answer


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    user_contexts[message.from_user.id] = []

    await message.answer(
        "Здравствуйте 🌙\n\n"
        "Я бот-консультант по китайской метафизике. "
        "Вы можете задать вопрос по Ба Цзы, Фэншуй или И Цзин.\n\n"
        "Выберите тему ниже или просто напишите свой вопрос.",
        reply_markup=main_keyboard(),
    )


@router.message(F.text == "🔮 Задать вопрос Ба Цзы")
async def bazi_button_handler(message: Message) -> None:
    await message.answer(
        "Для разбора Ба Цзы напишите, пожалуйста:\n\n"
        "1. Дату рождения\n"
        "2. Точное время рождения\n"
        "3. Город рождения\n"
        "4. Пол\n\n"
        "И сам вопрос, который вас интересует."
    )


@router.message(F.text == "🏡 Совет по Фэншуй")
async def fengshui_button_handler(message: Message) -> None:
    await message.answer(
        "Опишите помещение или ситуацию:\n\n"
        "1. Комната или зона дома\n"
        "2. Что хотите улучшить\n"
        "3. Примерное расположение двери, окон, кровати или стола\n\n"
        "Я дам мягкие практичные рекомендации."
    )


@router.message(F.text == "📜 Книга Перемен (И Цзин)")
async def iching_button_handler(message: Message) -> None:
    await message.answer(
        "Сформулируйте вопрос для И Цзин.\n\n"
        "Лучше задавать вопрос не в формате «что точно случится?», "
        "а в формате «какая энергия ситуации?» или «на что обратить внимание?»."
    )


@router.message(F.text)
async def gemini_dialog_handler(message: Message) -> None:
    await message.answer("Думаю над вашим вопросом...")

    try:
        answer = await ask_gemini(
            user_id=message.from_user.id,
            user_text=message.text,
        )
        await send_long_message(message, answer)
    except Exception as error:
        await message.answer(
            "Произошла ошибка при обращении к Gemini. "
            "Проверьте GEMINI_API_KEY, модель и попробуйте ещё раз."
        )
        print(f"Gemini error: {error}")
