import os

try:
    from dotenv import load_dotenv
    # Загрузка переменных из .env файла
    load_dotenv()
except ModuleNotFoundError:
    pass

# Чтение токена из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_TOKEN = os.getenv("WEATHER_TOKEN")
GIGA_CHAT_TOKEN = os.getenv("GIGA_CHAT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")
