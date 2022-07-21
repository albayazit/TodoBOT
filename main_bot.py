from config import TOKEN
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types

# FSM
storage=MemoryStorage()
class FSMdata(StatesGroup):
	name = State()
	description = State()


# инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)


# кнопка старт
tasks_button = KeyboardButton('📋 Задачи')
add_task = KeyboardButton('✏ Добавить задачу')
markup_main = ReplyKeyboardMarkup(resize_keyboard=True)
markup_main.add(tasks_button).add(add_task)

@dp.message_handler(commands="start")
async def start_command(message : types.Message):
	await message.answer('Привет! Вот что я умею:', reply_markup=markup_main)


# кнопка список задач
@dp.message_handler(lambda message: message.text == "📋 Задачи")
async def tasks_command(message : types.Message):
	await message.answer('Задачи:')


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
	await message.answer('Действие отменено')

@dp.message_handler(state=FSMdata.name)
async def set_name(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['name'] = message.text
	await FSMdata.next()
	await message.answer('Введите описание задачи:')

@dp.message_handler(state=FSMdata.description)
async def set_description(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['description'] = message.text

	async with state.proxy() as data:
		await message.answer(str(data))
	await state.finish()


# поллинг
if __name__ == '__main__':
  executor.start_polling(dp,skip_updates=True)
