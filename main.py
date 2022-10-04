from decouple import config
from aiogram import Bot, Dispatcher, executor, types
from pyqiwip2p import QiwiP2P
from repository.user_repository import UserRepositoryDB
from repository.check_repository import CheckRepositoryDB
from model.user import User
from controllers.start_controller import StartController
from controllers.admin_controller import AdminController
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from typing import Union
import logging.config
from logging_config import dict_config


TOKEN = config('TOKEN')
bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

p2p = QiwiP2P(auth_key=config('PRIVATE_KEY'))

ADMIN = config('ADMIN')

user_repository_db = UserRepositoryDB()
check_repository_db = CheckRepositoryDB()

start_controller = StartController(bot=bot, user_repository_db=user_repository_db,
                                   check_repository_db=check_repository_db, p2p=p2p)
admin_controller = AdminController(bot=bot, user_repository_db=user_repository_db,
                                   check_repository_db=check_repository_db, p2p=p2p, admin=ADMIN)

logging.config.dictConfig(dict_config)
logger = logging.getLogger('main')
logger.setLevel('DEBUG')

# logging.basicConfig(level='ERROR', format='%(asctime)s %(levelname)s:%(message)s')
# logger = logging.getLogger('main')
# logger.setLevel(level='DEBUG')
#
# file_handler_error = logging.FileHandler('logfile.log')
# file_handler_error.setLevel(level='ERROR')
#
# file_handler_info = logging.FileHandler('logfile.log')
# file_handler_info.setLevel(level='DEBUG')
#
# console_handler = logging.StreamHandler()
# console_handler.setLevel(level='DEBUG')
#
# logger.addHandler(file_handler_error)
# logger.addHandler(file_handler_info)
# logger.addHandler(console_handler)


class Form(StatesGroup):
    money = State()
    user_id_blacklist = State()
    user_id_reduce_money = State()
    reduce_money = State()


@dp.message_handler(commands='start')
async def start_command(message: types.Message) -> None:
    logger.debug('Start process start_command')

    try:
        user = user_repository_db.get_user(message.from_user.id)

        text = 'Вы были забанены Администрацией!'

        if user.block == 1:
            await bot.send_message(message.from_user.id, text=text)
        else:
            await start_controller.process_start(message)

    except TypeError as error:
        logger.info(f'user id: {message.from_user.id}')
        logger.exception('This user was not found in the database', exc_info=error)

        user_repository_db.set_user(User(user_id=message.from_user.id, user_name=message.from_user.first_name))
        await start_controller.process_start(message)


@dp.message_handler(commands='admin')
async def admin_command(message: types.Message) -> None:
    text = 'Вы не являетесь адмистратором! Введите команду /start'

    if message.from_user.id == int(ADMIN):
        await admin_controller.process_admin(message)
    else:
        await bot.send_message(message.from_user.id, text=text)


@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.money)
async def top_up_invalid(message: types.Message) -> types.Message:
    text = 'Введите целое число. Минимальная сумма для пополнения 1 руб.'

    return await bot.send_message(message.from_user.id, text=text)


@dp.message_handler(state=Form.money)
async def top_up_callback(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['money'] = message.text
    await start_controller.top_up_callback(message)
    await state.finish()


@dp.message_handler(state=Form.user_id_blacklist)
async def blacklist_callback(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['user_id_blacklist'] = message.text
    await admin_controller.blacklist_callback(message)
    await state.finish()


@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.user_id_reduce_money)
async def user_id_reduce_money_invalid(message: types.Message) -> types.Message:
    text = 'Вы вводите буквы!\nID состоит из цифр. Попробуйте снова.'

    return await bot.send_message(message.from_user.id, text=text)


@dp.message_handler(state=Form.user_id_reduce_money)
async def user_id_reduce_money_callback(message: types.Message, state: FSMContext) -> Union[None, types.Message]:
    logger.debug('Start process user_id_reduce_money_callback')

    text_1 = 'Введите сумму на которую нужно уменьшить баланс пользоваетля'
    text_2 = 'Такой пользователь не найден в базе данных. Попробуйте снова.'

    try:
        user_repository_db.get_user(message.text)

        async with state.proxy() as data:
            data['user_id_reduce_money'] = message.text

        await Form.next()

        await bot.send_message(message.from_user.id, text=text_1)

    except TypeError as error:
        logger.info(f'user id: {message.from_user.id}')
        logger.exception('This user was not found in the database', exc_info=error)

        return await bot.send_message(message.from_user.id, text=text_2)


@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.reduce_money)
async def reduce_money_invalid(message: types.Message) -> types.Message:
    text = 'Сумма должен быть числом! Попробуйте еще раз.'

    return await bot.send_message(message.from_user.id, text=text)


@dp.message_handler(state=Form.reduce_money)
async def user_id_reduce_money_callback(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['reduce_money'] = message.text
    await admin_controller.reduce_money_callback(message, data['user_id_reduce_money'], data['reduce_money'])
    await state.finish()


@dp.callback_query_handler(text='top_up')
async def top_up(call: types.CallbackQuery) -> None:
    text = 'Введите сумму, на которую Вы хотите пополнить баланс'

    await Form.money.set()
    await bot.send_message(call.from_user.id, text=text)


@dp.callback_query_handler(text_contains='check_')
async def check(call: types.CallbackQuery) -> None:
    await start_controller.check_callback(call)


@dp.callback_query_handler(text='get_users')
async def get_users(call: types.CallbackQuery) -> None:
    await admin_controller.get_users_callback(call)


@dp.callback_query_handler(text='get_logs')
async def get_logs(call: types.CallbackQuery) -> None:
    await admin_controller.get_logs_callback(call)


@dp.callback_query_handler(text='change_balance')
async def change_balance(call: types.CallbackQuery) -> None:
    text = 'Вы хотите уменьшить или увеличить баланс пользователя?'

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    reduce_money = types.InlineKeyboardButton(text='Уменьшить баланс', callback_data='reduce_money')
    increase_money = types.InlineKeyboardButton(text='Увеличить баланс', callback_data='increase_money')

    keyboard.add(reduce_money, increase_money)

    await bot.send_message(call.from_user.id, text=text, reply_markup=keyboard)


@dp.callback_query_handler(text='blacklist')
async def blacklist(call: types.CallbackQuery) -> None:
    text = 'Введите id пользователя, которого нужно заблокировать'

    await Form.user_id_blacklist.set()
    await bot.send_message(call.from_user.id, text=text)


@dp.callback_query_handler(text='reduce_money')
async def reduce_money(call: types.CallbackQuery) -> None:
    text = 'Введите id пользователя у которого нужно уменьшить баланс'

    await Form.user_id_reduce_money.set()
    await bot.send_message(call.from_user.id, text=text)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
