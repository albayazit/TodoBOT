from config import TOKEN
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# клавиатуры
markup_main = InlineKeyboardMarkup().add(InlineKeyboardButton('Добавить предмет', callback_data='add_object'))

# старт
@dp.message_handler(commands="start")
async def start_command(message : types.Message):
	await message.answer('Предметы:', reply_markup=markup_main)

# поллинг
if __name__ == '__main__':
  executor.start_polling(dp,skip_updates=True)
