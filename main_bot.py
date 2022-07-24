from email import message
from email.errors import MissingHeaderBodySeparatorDefect
from faulthandler import cancel_dump_traceback_later
from config import TOKEN
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types
import sqlite3 as sq

# функция при старте
async def on_startup(_):
	print('Bot online')
	sql_start()


# FSM
storage=MemoryStorage()
class FSMdata(StatesGroup):
	name = State()
	description = State()

# database
def sql_start():
	global base, cur
	base = sq.connect('database.db')
	cur = base.cursor()
	base.execute('''CREATE TABLE IF NOT EXISTS data(
		task_id TEXT,
		user_id TEXT,
		name TEXT, 
		description TEXT
		)''')
	base.commit()



# инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

# кнопка старт
tasks_button = KeyboardButton('📋 Задачи')
add_task = KeyboardButton('✏ Добавить задачу')
markup_main = ReplyKeyboardMarkup(resize_keyboard=True)
markup_main.add(tasks_button).add(add_task)
markup_tasks= InlineKeyboardMarkup()

@dp.message_handler(commands="start")
async def start_command(message : types.Message):
	await message.answer('Привет! Вот что я умею:', reply_markup=markup_main)

# отображения задач
def tasks_markup(user_id):
	task = 0
	markup_tasks = InlineKeyboardMarkup()
	for item in cur.execute(f'SELECT name FROM data WHERE user_id == {user_id}').fetchall():
		task += 1
		markup_tasks.add(InlineKeyboardButton(item[0], callback_data=task))
	return markup_tasks


# отображение описания
# def tasks_desc(user_id, current_task):
# 	markup_desc = InlineKeyboardMarkup


# кнопка список задач
@dp.message_handler(lambda message: message.text == "📋 Задачи")
async def tasks_command(message : types.Message):
	user_id = message.from_user.id
	await message.answer('Задачи:', reply_markup=tasks_markup(user_id))

# описание к задаче
@dp.callback_query_handler(text=range(1000))
async def task_description(callback: types.CallbackQuery):
	user_id = callback.from_user.id
	current_task = callback.data
	text = cur.execute(f'SELECT description FROM data WHERE user_id == {user_id} AND task_id == {current_task}').fetchone()
	await callback.message.answer(text[0])
	await callback.answer()

# кнопка добавить задачу
@dp.message_handler(lambda message: message.text == "✏ Добавить задачу", state=None)
async def add_task_command(message: types.Message):
	await FSMdata.name.set()
	await message.answer('Введите название задачи:')


@dp.message_handler(commands='cancel', state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
	current_state = await state.get_state()
	if current_state is None:
		return
	await state.finish()
	await message.answer('Действие отменено ❌')

@dp.message_handler(state=FSMdata.name)
async def set_name(message: types.Message, state: FSMContext):
	user_id = message.from_user.id
	tasks = 0
	for item in cur.execute(f'SELECT task_id FROM data WHERE user_id == {user_id}').fetchall():
		tasks += 1
	async with state.proxy() as data:
		cur.execute('INSERT INTO data VALUES (?, ?, ?, ?)', (str(tasks+1), user_id, str(message.text), 'Описание отсутствует'))
		base.commit()
	await message.answer('Задача успешно добавлена ✅')
	await state.finish()

# поллинг
if __name__ == '__main__':
  executor.start_polling(dp,skip_updates=True, on_startup=on_startup)