# Chinese Metaphysics Telegram Bot

Telegram-бот по китайской метафизике на Python.

Стек:

- Python 3.10+
- aiogram 3.x
- OpenAI API
- модель `gpt-4o`

## Возможности

- команда `/start`;
- кнопки:
  - 🔮 Задать вопрос Ба Цзы;
  - 🏡 Совет по Фэншуй;
  - 📜 Книга Перемен (И Цзин);
- системный промт эксперта по китайской метафизике;
- сохранение краткого контекста беседы в памяти процесса;
- безопасная работа с ключами через `.env`.

## Локальный запуск на macOS

Открой терминал в VS Code и выполни:

```bash
git clone https://github.com/Valenciaqwe/meta.git
cd meta
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Открой файл `.env` и вставь свои ключи:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
```

Запуск:

```bash
python main.py
```

## Важно про безопасность

Файл `.env` добавлен в `.gitignore`. Не загружай настоящие токены Telegram и OpenAI в GitHub.

## Структура проекта

```text
.
├── main.py
├── config.py
├── handlers.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
