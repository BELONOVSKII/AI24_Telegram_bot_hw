from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from states import Form

from utils import (
    get_calories_goal,
    get_water_goal,
    get_weather_asynch,
    get_calories_async,
    water_progress_template,
    calories_progress_template,
)

router = Router()

_id = 0
_data_base = {}


async def insert_data(data):
    weather = await get_weather_asynch(data["city"])
    water_goal = get_water_goal(data["weight"], data["activity_minutes"], weather)
    calories_goal = get_calories_goal(
        data["weight"], data["activity_minutes"], data["height"], data["age"]
    )

    global _id, _data_base
    _data_base[_id] = {
        **data,
        "water_goal": water_goal,
        "calories_goal": calories_goal,
        "logged_water": 0.0,
        "logged_calories": 0.0,
        "burned_calories": 0.0,
    }


# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(
        "Добро пожаловать! Я ваш бот.\nГотов помочь вам следить за здоровьем."
    )


# Получаем данные о пользователе /set_profile
@router.message(Command("set_profile"))
async def start_form(message: Message, state: FSMContext):
    await message.answer("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)


@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    weight = message.text
    try:
        weight = float(weight)
    except ValueError:
        await message.reply("Введен не правильный вес. Попробуйте еще раз.")
        await message.answer("Введите ваш вес (в кг):")
        return

    await state.update_data(weight=weight)
    await message.answer("Введите ваш рост (в см):")
    await state.set_state(Form.height)


@router.message(Form.height)
async def process_height(message: Message, state: FSMContext):
    height = message.text
    try:
        height = float(height)
    except ValueError:
        await message.reply("Введен не правильный рост. Попробуйте еще раз.")
        await message.answer("Введите ваш рост (в см):")
        return

    await state.update_data(height=height)
    await message.answer("Введите ваш возраст:")
    await state.set_state(Form.age)


@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    age = message.text
    try:
        age = int(age)
    except ValueError:
        await message.reply("Введен не правильный возраст. Попробуйте еще раз.")
        await message.answer("Введите ваш возраст:")
        return

    await state.update_data(age=age)
    await message.answer("Сколько минут активности у вас в день?")
    await state.set_state(Form.activity_minutes)


@router.message(Form.activity_minutes)
async def process_activity_minutes(message: Message, state: FSMContext):
    activity_minutes = message.text
    try:
        activity_minutes = float(activity_minutes)
    except ValueError:
        await message.reply(
            "Введено не правильное количество минут активности. Попробуйте еще раз."
        )
        await message.answer("Сколько минут активности у вас в день?")
        return

    await state.update_data(activity_minutes=activity_minutes)
    await message.answer("В каком городе вы находитесь?")
    await state.set_state(Form.city)


@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Параметры заданы успешно!")
    data = await state.get_data()
    await insert_data(data)
    await state.clear()


# Логгируем воду /log_water
@router.message(Command("log_water"))
async def log_water(message: Message, command: CommandObject):
    water_consumed = command.args

    if water_consumed is None:
        await message.reply("Пожалуйста введите количество выпитой воды")
        return
    try:
        water_consumed = float(water_consumed)
    except ValueError:
        await message.reply("Пожалуйста введите корректное количество выпитой воды")
        return

    _data_base[_id]["logged_water"] += water_consumed

    await message.answer(
        f'Всего выпито воды: {_data_base[_id]["logged_water"]}. Цель: {_data_base[_id]["water_goal"]}.'
    )
    await message.answer(
        f'Отсалось выпить: {max(0, _data_base[_id]["water_goal"] - _data_base[_id]["logged_water"])}.'
    )


# Логгируем еду /log_food
@router.message(Command("log_food"))
async def log_food(message: Message, command: CommandObject):
    try:
        food_consumed, grams_consumed = command.args.split(" ")
        grams_consumed = float(grams_consumed)
    except (AttributeError, ValueError):
        await message.reply(
            "Пожалуйста введите название и корректный вес продукта, который вы съели"
        )
        return

    calories_consumed = float(await get_calories_async(food_consumed))
    _data_base[_id]["logged_calories"] += calories_consumed * (grams_consumed / 100)

    await message.answer(f"{food_consumed} - {calories_consumed} ккал на 100 г.")
    await message.answer(
        f"{calories_consumed * (grams_consumed / 100):.3f} ккал всего. Данные записаны."
    )


# Логгируем тренировку /log_workout
@router.message(Command("log_workout"))
async def log_workout(message: Message, command: CommandObject):
    try:
        workout_type, workout_time = command.args.split(" ")
        workout_time = float(workout_time)
    except (AttributeError, ValueError):
        await message.reply(
            "Пожалуйста введите название трнировки и корректную продолжительность тренировки."
        )
        return

    _data_base[_id]["burned_calories"] += 300

    await message.answer(
        f"{workout_type} {workout_time} минут — 300 ккал."
        + (
            f" Дополнительно: выпейте {200 * (workout_time // 30)} мл воды."
            if workout_time >= 30
            else ""
        )
    )


# Показываем прогресс /check_progress
@router.message(Command("check_progress"))
async def check_progress(message: Message):
    # water
    await message.answer(
        water_progress_template.format(
            _data_base[_id]["logged_water"],
            _data_base[_id]["water_goal"],
            max(_data_base[_id]["water_goal"] - _data_base[_id]["logged_water"], 0),
        )
    )

    # calories
    await message.answer(
        calories_progress_template.format(
            _data_base[_id]["logged_calories"],
            _data_base[_id]["calories_goal"],
            _data_base[_id]["burned_calories"],
            _data_base[_id]["logged_calories"] - _data_base[_id]["burned_calories"],
        )
    )


# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)
