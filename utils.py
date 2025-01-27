import aiohttp
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat

from config import WEATHER_TOKEN
from config import GIGA_CHAT_TOKEN

giga = GigaChat(credentials=GIGA_CHAT_TOKEN, verify_ssl_certs=False, model="GigaChat")
messages = [
    SystemMessage(
        content="""Ты экспертный диетолог. Тебе на вход передадут название продукта, который съел клиент.
        Ты должен вернуть количество калорий на 100 г. соответсвующее этому продукту. Ответ должен быть одинм числом."""
    )
]
URL_TEMPLATE = "https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={token}"


def get_water_goal(weight, activity, weather):
    return float(30 * weight + 500 * activity // 30 + 500 * int(weather >= 25))


def get_calories_goal(weight, activity, height, age):
    return float(10 * weight + 6.25 * height - 5 * age + 200 * int(activity > 0))


async def get_weather_asynch(city):
    url = URL_TEMPLATE.format(city=city, token=WEATHER_TOKEN)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            return float(json.loads(content)["main"]["temp"])


async def get_calories_async(food):
    res = await giga.ainvoke(messages + [HumanMessage(content=food)])
    return res.content


water_progress_template = """
Вода:
- Выпито: {0} мл из {1} мл.
- Осталось: {2} мл.
"""

calories_progress_template = """
Калории:
- Потреблено: {0} ккал из {1} ккал.
- Сожжено: {2} ккал.
- Баланс: {3} ккал.
"""
