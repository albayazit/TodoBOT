from ast import parse
from email import message
from email.errors import MissingHeaderBodySeparatorDefect
from faulthandler import cancel_dump_traceback_later
from tabnanny import check
from time import sleep
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
markup_main = ReplyKeyboardMarkup(resize_keyboard=True)
markup_main.add(tasks_button).add(add_task)
delete_btn = InlineKeyboardButton('Удалить', callback_data='delete')
edit_btn = InlineKeyboardButton('Изменить описание', callback_data='edit')
desc_inline = InlineKeyboardMarkup().insert(delete_btn).insert(edit_btn)
next_btn = InlineKeyboardButton('»', callback_data='next_btn')
back_btn = InlineKeyboardButton('«', callback_data='back_btn')
global page
page = 1

# кнопка старт
@dp.message_handler(commands="start")
async def start_command(message : types.Message):
	await message.answer('<b>Привет!</b>', reply_markup=markup_main)


# кнопка помощь
@dp.message_handler(commands="help")
async def help_command(message : types.Message):
	await message.answer('Бот предназначен для отслеживания ваших задач!\n<b>Выберите раздел:</b>', reply_markup=markup_main)


# отображения задач
def tasks_markup(user_id, page):
	markup_tasks = InlineKeyboardMarkup(row_width=2)
	items = page * 10
	count = 0
	check = cur.execute(f'SELECT name FROM data WHERE user_id == {user_id}').fetchall()
	x = 0
	for j in check:
		x += 1
	for item in range(items-10, items):
		for i in cur.execute(f'SELECT name FROM data WHERE user_id == {user_id} AND task_id == {item}').fetchall():
			count += 1
			markup_tasks.insert(InlineKeyboardButton(i[0], callback_data=str(item)))
	if count == 10 and page == 1 and x > 10:
		markup_tasks.add(next_btn)
	elif count % 10 == 0 and page != 1:
		markup_tasks.add(back_btn)
		markup_tasks.insert(next_btn)
	elif count % 10 != 0 and page != 1:
		markup_tasks.add(back_btn)

	# elif page == 1 and last_page == False and count == 10:
	# 	markup_tasks.add(next_btn)
	# elif last_page == False and page != 1:
	# 	markup_tasks.insert(back_btn)
	# 	markup_tasks.insert(next_btn)
	# elif last_page == True:
	# 	markup_tasks.add(back_btn)
	return markup_tasks

@dp.callback_query_handler(text = 'next_btn')
async def next_cmd(callback: types.CallbackQuery):
	user_id = callback.from_user.id
	global page
	page += 1
	await callback.message.edit_text('■□■□■□■□■□ <b>TASKS</b> □■□■□■□■□■', reply_markup=tasks_markup(user_id, page))
	await callback.answer()

@dp.callback_query_handler(text = 'back_btn')
async def back_cmd(callback: types.CallbackQuery):
	user_id = callback.from_user.id
	global page
	page -= 1
	await callback.message.edit_text('■□■□■□■□■□ <b>TASKS</b> □■□■□■□■□■', reply_markup=tasks_markup(user_id, page))
	await callback.answer()

# кнопка список задач
@dp.message_handler(lambda message: message.text == "📋 Задачи") 
async def tasks_command(message : types.Message):
	global page
	page = 1
	user_id = message.from_user.id
	await message.answer('■□■□■□■□■□ <b>TASKS</b> □■□■□■□■□■', reply_markup=tasks_markup(user_id, page))

# описание к задаче
@dp.callback_query_handler(text=range(1000))
async def task_description(callback: types.CallbackQuery):
	user_id = callback.from_user.id
	global current_task
	current_task = callback.data
	check = cur.execute(f'SELECT task_id FROM data WHERE user_id == {user_id}').fetchall()
	inmas = False
	for i in check:
		if current_task == i[0]:
			inmas = True
			break
		else:
			inmas = False
	if inmas == True:
		name = cur.execute('SELECT name FROM data WHERE user_id == ? AND task_id == ?', (user_id, current_task)).fetchone()
		task_name = f'Задача: <b>{name[0]}</b>\n'
		text = cur.execute(f'SELECT description FROM data WHERE user_id == ? AND task_id == ?', (user_id, current_task)).fetchone()
		await callback.message.edit_text(task_name + text[0], reply_markup=desc_inline)
	else:
			await callback.message.answer('Задача удалена.', reply_markup=markup_main)
			await callback.answer()


# удаление задачи
@dp.callback_query_handler(text='delete')
async def task_delete(callback: types.CallbackQuery):
	user_id = callback.from_user.id
	task = -1
	cur.execute(f'DELETE FROM data WHERE user_id == ? AND task_id == ?', (user_id, current_task))
	base.commit()
	for item in cur.execute(f'SELECT task_id FROM data WHERE user_id == {user_id}').fetchall():
		task += 1
		try:
			cur.execute('UPDATE data SET task_id = ? WHERE user_id == ? AND task_id == ?', (task, user_id, item[0]))
			base.commit()
		except:
			await callback.message.edit_text('Ой, что-то пошло не так! Повторите еще раз!', reply_markup=markup_main)
	await callback.message.edit_text('Задача успешно удалена ✅')
	await callback.answer()


# изменение описания
@dp.callback_query_handler(text='edit', state=None)
async def task_edit(callback : types.CallbackQuery):
	await FSMdata.description.set()
	await callback.message.answer('Введите новое описание:')
	await callback.answer()

@dp.message_handler(state=FSMdata.description)
async def set_desc(message: types.Message, state: FSMContext):
	user_id = message.from_user.id
	cur.execute('UPDATE data SET description = ? WHERE user_id = ? AND task_id = ?', (str(message.text), user_id, current_task))
	base.commit()
	await message.answer('Описание успешно изменено ✅', reply_markup=markup_main)
	await state.finish()


# кнопка добавить задачу
@dp.message_handler(lambda message: message.text == "✏ Добавить задачу",state=None)
async def add_task_command(message: types.Message):
	await FSMdata.name.set()
	await message.answer('Введите название задачи:', reply_markup=types.ReplyKeyboardRemove())

# отмена FSM
@dp.message_handler(commands='cancel', state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
	current_state = await state.get_state()
	if current_state is None:
		return
	await state.finish()
	await message.edit_text('Действие отменено ❌')

# добавление новой задачи
@dp.message_handler(state=FSMdata.name)
async def set_name(message: types.Message, state: FSMContext):
	user_id = message.from_user.id
	task = -1
	for item in cur.execute(f'SELECT task_id FROM data WHERE user_id == {user_id}').fetchall():
		task += 1
	try:
		cur.execute('INSERT INTO data VALUES (?, ?, ?, ?)', (str(task+1), user_id, str(message.text), 'Описание отсутствует'))
		base.commit()
		await message.answer('Задача успешно добавлена ✅', reply_markup=markup_main)
	except:
		await message.answer('Ой, что-то пошло не так! Повторите еще раз!', reply_markup=markup_main)
	await state.finish()

# реакция на остальные сообщения
@dp.message_handler()
async def unknown_command(message : types.Message):
	await message.answer('Я тебя не понимаю.\n<b>Выберите раздел:</b>', reply_markup=markup_main)


# поллинг
if __name__ == '__main__':
  executor.start_polling(dp,skip_updates=True, on_startup=on_startup)