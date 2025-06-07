import logging
from aiogram import Bot, Dispatcher, executor, types
import requests

# Настройки
TELEGRAM_TOKEN = '8171020038:AAGAVYTjsQ7ISn01gTZhykY6c2oShgbpS2I'
OPENROUTER_API_KEY = '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'
DEEPSEEK_API_KEY = 'sk-323aec6cc73a49e29229b4c70a87b63a'

# Инициализация
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# URL и заголовки для OpenRouter
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
openrouter_headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

# URL и заголовки для DeepSeek
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
deepseek_headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}


# Запрос к нейросети
async def ask_model(prompt, use_deepseek=False):
    if use_deepseek:
        url = DEEPSEEK_URL
        headers = deepseek_headers
        model = "deepseek-chat"
    else:
        url = OPENROUTER_URL
        headers = openrouter_headers
        model = "openai/gpt-3.5-turbo"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"❌ Ошибка при запросе к API: {e}")
        return "Ошибка при подключении к нейросети."


# Обработка кнопки
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("💡 Спросить через OpenRouter", "🧠 Спросить через DeepSeek")
    await message.answer("Выбери режим:", reply_markup=kb)


# Основная логика
@dp.message_handler(lambda m: m.text.startswith("💡") or m.text.startswith("🧠"))
async def process_question(message: types.Message):
    await message.answer("Введите ваш вопрос:")


# Ответ на сообщение
@dp.message_handler()
async def handle_message(message: types.Message):
    if message.reply_to_message and message.reply_to_message.text.startswith("Введите ваш вопрос"):
        use_deepseek = message.reply_to_message.text.startswith("🧠")
    else:
        use_deepseek = False
    await message.answer("🔄 Думаю...")
    answer = await ask_model(message.text, use_deepseek=use_deepseek)
    await message.answer(answer)


if __name__ == '__main__':
    print("🤖 ГОЙДААА!")
    executor.start_polling(dp, skip_updates=True)
