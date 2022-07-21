from config import TOKEN
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# старт
tasks_button = KeyboardButton('📋 Задачи')
add_task = KeyboardButton('✏ Добавить задачу')

markup_main = ReplyKeyboardMarkup(resize_keyboard=True)
markup_main.add(tasks_button).add(add_task)

@dp.message_handler(commands="start")
async def start_command(message : types.Message):
	await message.answer('Привет! Вот что я умею:', reply_markup=markup_main)

# список задач

@dp.message_handler(lambda message: message.text == "📋 Задачи")
async def tasks_command(message : types.Message):
	await message.answer('Задачи:')

# поллинг
if __name__ == '__main__':
  executor.start_polling(dp,skip_updates=True)
