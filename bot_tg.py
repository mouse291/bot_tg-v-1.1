import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from dotenv import load_dotenv
import requests

# Загрузка переменных из .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Настройки для webhook
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # Пример: https://your-app-name.onrender.com
WEBHOOK_PATH = f"/webhook/{TELEGRAM_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))

# Инициализация
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# URL и заголовки для моделей
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

openrouter_headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}
deepseek_headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}


# Функция запроса к модели
async def ask_model(prompt, use_deepseek=False):
    headers = deepseek_headers if use_deepseek else openrouter_headers
    url = DEEPSEEK_URL if use_deepseek else OPENROUTER_URL
    model = "deepseek-chat" if use_deepseek else "openai/gpt-3.5-turbo"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"❌ Ошибка при запросе к API: {e}")
        return "Ошибка при подключении к нейросети."


# Команда /start
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("💡 OpenRouter", "🧠 DeepSeek")
    await message.answer("Выбери модель:", reply_markup=kb)


# Переменная режима
user_modes = {}


@dp.message_handler(lambda m: m.text in ["💡 OpenRouter", "🧠 DeepSeek"])
async def choose_mode(message: types.Message):
    use_ds = message.text.startswith("🧠")
    user_modes[message.from_user.id] = use_ds
    await message.answer("Теперь отправьте свой вопрос.")


# Режим логов по паролю
@dp.message_handler(lambda m: m.text.startswith("/logs"))
async def get_logs(message: types.Message):
    parts = message.text.split()
    if len(parts) == 2 and parts[1] == ADMIN_PASSWORD:
        await message.answer("Логов нет или режим логов отключен (пока заглушка).")
    else:
        await message.answer("Неверный пароль.")


# Обработка текстовых сообщений
@dp.message_handler()
async def main_handler(message: types.Message):
    use_ds = user_modes.get(message.from_user.id, False)
    await message.answer("🕐 Думаю...")
    reply = await ask_model(message.text, use_deepseek=use_ds)
    await message.answer(reply)


# Webhook-режим запуска
async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("🚀 Webhook установлен")


async def on_shutdown(dispatcher):
    await bot.delete_webhook()
    logging.info("🛑 Webhook удалён")


if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )

