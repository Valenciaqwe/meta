from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from openai import OpenAI

from config import settings

router = Router()

client = OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

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


async def ask_gpt(user_id: int, user_text: str) -> str:
    history = get_user_history(user_id)
    history.append({"role": "user", "content": user_text})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-12:]

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
    )

    answer = response.choices[0].message.content or "Не удалось получить ответ от модели."
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
async def gpt_dialog_handler(message: Message) -> None:
    await message.answer("Думаю над вашим вопросом...")

    try:
        answer = await ask_gpt(
            user_id=message.from_user.id,
            user_text=message.text,
        )
        await message.answer(answer)
    except Exception as error:
        await message.answer(
            "Произошла ошибка при обращении к модели. "
            "Проверьте ключ OpenRouter API, модель и попробуйте ещё раз."
        )
        print(f"Model error: {error}")
