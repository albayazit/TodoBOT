from ast import parse
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
bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)


# основные переменные
tasks_button = KeyboardButton('📋 Задачи')
add_task = KeyboardButton('✏ Добавить задачу')
markup_main = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
markup_main.add(tasks_button).add(add_task)
markup_tasks= InlineKeyboardMarkup()
delete_btn = InlineKeyboardButton('Удалить', callback_data='delete')
edit_btn = InlineKeyboardButton('Изменить описание', callback_data='edit')
desc_inline = InlineKeyboardMarkup().insert(delete_btn).insert(edit_btn)
desc_message = ''

# кнопка старт
@dp.message_handler(commands="start")
async def start_command(message : types.Message):
	await message.answer('<b>Hi!</b>', reply_markup=markup_main)


# кнопка помощь
@dp.message_handler(commands="help")
async def help_command(message : types.Message):
	await message.answer('The bot is designed to track daily tasks and add descriptions to them.\n<b>Select a section:</b>', reply_markup=markup_main)


# отображения задач
def tasks_markup(user_id):
	markup_tasks = InlineKeyboardMarkup()
	task = 0
	for item in cur.execute(f'SELECT name FROM data WHERE user_id == {user_id}').fetchall():
		task += 1
		markup_tasks.add(InlineKeyboardButton(item[0], callback_data=str(task)))
	return markup_tasks


# кнопка список задач
@dp.message_handler(lambda message: message.text == "📋 Задачи", commands='tasks')
async def tasks_command(message : types.Message):
	user_id = message.from_user.id
	await message.answer('<b>Tasks:</b>', reply_markup=tasks_markup(user_id))


# описание к задаче
@dp.callback_query_handler(text=range(1000))
async def task_description(callback: types.CallbackQuery):
	user_id = callback.from_user.id
	global current_task
	current_task = callback.data
	text = cur.execute(f'SELECT description FROM data WHERE user_id == {user_id} AND task_id == {current_task}').fetchone()
	await callback.message.edit_text(text[0], reply_markup=desc_inline)
	await callback.answer()

# удаление задачи
@dp.callback_query_handler(text='delete')
async def task_delete(callback: types.CallbackQuery):
	user_id = callback.from_user.id
	task = 0
	cur.execute(f'DELETE FROM data WHERE user_id == {user_id} AND task_id == {current_task}')
	base.commit()
	for item in cur.execute(f'SELECT task_id FROM data WHERE user_id == {user_id}').fetchall():
		task += 1
		try:
			cur.execute('UPDATE data SET task_id = ? WHERE user_id == ? AND task_id == ?', (task, user_id, item[0]))
			base.commit()
			await callback.message.edit_text('Задача успешно удалена ✅')
		except:
			await callback.message.edit_text('Ой, что-то пошло не так! Повторите еще раз!', reply_markup=markup_main)
	await callback.answer()


# изменение описания
@dp.callback_query_handler(text='edit', state=None)
async def task_edit(callback : types.CallbackQuery):
	await FSMdata.description.set()
	await callback.message.answer('Введите описание к задаче:')
	await callback.answer()

@dp.message_handler(state=FSMdata.description)
async def set_desc(message: types.Message, state: FSMContext):
	user_id = message.from_user.id
	try:
		cur.execute('UPDATE data SET description = ? WHERE user_id = ? AND task_id = ?', (str(message.text), user_id, current_task))
		base.commit()
		await message.answer('Описание успешно добавлено ✅', reply_markup=markup_main)
	except:
		await message.answer('Ой, что-то пошло не так! Повторите еще раз!', reply_markup=markup_main)
	await state.finish()


# кнопка добавить задачу
@dp.message_handler(lambda message: message.text == "✏ Добавить задачу",state=None)
async def add_task_command(message: types.Message):
	await FSMdata.name.set()
	await message.answer('Введите название задачи:')

# отмена FSM
@dp.message_handler(commands='cancel', state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
	current_state = await state.get_state()
	if current_state is None:
		return
	await state.finish()
	await message.answer('Действие отменено ❌')

# добавление новой задачи
@dp.message_handler(state=FSMdata.name)
async def set_name(message: types.Message, state: FSMContext):
	user_id = message.from_user.id
	task = 0
	for item in cur.execute(f'SELECT task_id FROM data WHERE user_id == {user_id}').fetchall():
		task += 1
	try:
		cur.execute('INSERT INTO data VALUES (?, ?, ?, ?)', (str(task+1), user_id, str(message.text), 'Описание отсутствует'))
		base.commit()
		await message.answer('Задача успешно добавлена ✅', reply_markup=markup_main)
	except:
		await message.answer('Ой, что-то пошло не так! Повторите еще раз!', reply_markup=markup_main)
	await state.finish()


# поллинг
if __name__ == '__main__':
  executor.start_polling(dp,skip_updates=True, on_startup=on_startup)