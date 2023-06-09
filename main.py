from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types.bot_command_scope import BotCommandScopeChat, BotCommandScopeDefault
import psycopg2
import os
import logging
import pandas as pd
import requests
import re

conn = psycopg2.connect(
    database="db",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)


bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(commands=['get_id'])
async def chat_id(message: Message):
    await message.answer(message.chat.id)


class States(StatesGroup):
    Manage_Start = State()
    Manage_Cont = State()
    Manage_Rate = State()
    Manage_Add = State()

    Start_Con = State()
    Next_Con = State()
    Cont_Con = State()


param = {}


def select_admin():
    cur = conn.cursor()
    cur.execute("""SELECT * FROM admins WHERE id = 1""")
    df = pd.DataFrame(cur.fetchall())
    admin_id = df.iloc[0][1]
    conn.commit()
    return admin_id


ADMIN_ID = select_admin()

user_commands = [
    types.BotCommand(command="/start", description="Старт"),
    types.BotCommand(command="/convert", description="Конвертация")
]

admin_commands = [
    types.BotCommand(command="/start", description="Старт"),
    types.BotCommand(command="/manage_currency", description="Админ панель"),
    types.BotCommand(command="/convert", description="Конвертировать")
]


async def setup_bot_commands(arg):
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_ID))


@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.answer("Привет, для того чтобы конвертировать валюты введите: - /convert")


@dp.message_handler(commands=['manage_currency'])
async def manage(message: Message):
    if str(message.chat.id) != ADMIN_ID:
        await message.answer("У вас нет доступа к этой команде")
    else:
        await message.answer("Введите название конвертируемой валюты")
        await States.Manage_Start.set()


@dp.message_handler(state=States.Manage_Start)
async def add_currency(message: Message, state: FSMContext):
    await state.update_data(baseCurrency=message.text)
    await message.answer("Введите название валюты, в которую можно конвертировать указанную ранее валюту")
    await States.Manage_Cont.set()


@dp.message_handler(state=States.Manage_Cont)
async def add_currency2(message: Message, state: FSMContext):
    await state.update_data(code=message.text)
    await message.answer("Введите курс")
    await States.Manage_Rate.set()


@dp.message_handler(state=States.Manage_Rate)
async def add_currency3(message: Message, state: FSMContext):
    d = await state.get_data()
    codee = d['code']
    try:
        ratess = d['rates']
    except Exception:
        ratess = []
    ratess.append({'code': codee, 'rate': float(message.text)})
    await state.update_data(rates=ratess)
    await message.answer("Добавить ещё валюту, в которую может быть сконвертирована валюта?(Да/Нет)")
    await States.Manage_Add.set()


@dp.message_handler(state=States.Manage_Add)
async def addition(message: Message, state: FSMContext):
    cur = await state.get_data()
    answer = message.text
    otvet = "Да"
    if otvet in answer:
        await message.answer("Введите название валюты, в которую будет производиться конвертация")
        await States.Manage_Cont.set()
    else:
        param["baseCurrency"] = str(cur["baseCurrency"])
        param["rates"] = cur["rates"]
        print(param)
        requests.post("http://localhost:10640/load", json=param)
        await message.answer("Вы завершили настройку")
        param.clear()
        await state.finish()


@dp.message_handler(commands=['convert'])
async def start(message: Message):
    await message.answer("Введите название конвертируемой валюты")
    await States.Start_Con.set()


@dp.message_handler(state=States.Start_Con)
async def process(message: types.Message, state: FSMContext):
    await state.update_data(baseCurrency=message.text)
    await States.Next_Con.set()
    await message.answer("Введите название валюты, в которую будет производиться конвертация")


@dp.message_handler(state=States.Next_Con)
async def convert(message: types.Message, state: FSMContext):
    await state.update_data(convertedCurrency=message.text)
    await States.Cont_Con.set()
    await message.answer("Введите сумму")


@dp.message_handler(state=States.Cont_Con)
async def convertion(message: types.Message, state: FSMContext):
    sum = message.text
    cur = await state.get_data()
    param["baseCurrency"] = str(cur["baseCurrency"])
    param["convertedCurrency"] = str(cur["convertedCurrency"])
    param["sum"] = float(sum)
    print(param)
    result = requests.get("http://localhost:10604/convert", params=param)
    print(result)
    if result == "<Response [500]":
        await message.answer("Ошибка")
        param.clear()
        await state.finish()
    else:
        print(result)
        res = result.text
        res = float(re.sub(r"[^0-9.]", r"", res))
        await message.answer(f'Результат конвертации({res})')
        param.clear()
        await state.finish()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dp.middleware.setup(LoggingMiddleware())
    executor.start_polling(dp, skip_updates=True, on_startup=setup_bot_commands)
