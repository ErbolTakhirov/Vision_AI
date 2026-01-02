import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# URL вашего Mini App (например, https://ващ-домен.ngrok.io)
# ВАЖНО: Telegram Mini Apps требуют HTTPS!
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://google.com") 

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start
    """
    kb = [
        [types.KeyboardButton(text="👁️ Открыть Vision Assistant", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        "Привет! Я Vision Assistant.\n"
        "Я помогу тебе распознать объекты вокруг.\n"
        "Нажми на кнопку ниже, чтобы запустить приложение.",
        reply_markup=keyboard
    )

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if not TOKEN or TOKEN == "your_telegram_bot_token_here":
        print("ОШИБКА: Укажите TELEGRAM_BOT_TOKEN в файле .env")
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("Бот остановлен")
