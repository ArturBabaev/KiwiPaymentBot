from aiogram import Bot, types
from pyqiwip2p import QiwiP2P
from repository.user_repository import UserRepositoryDB
from repository.check_repository import CheckRepositoryDB
import logging


logging.basicConfig(level='ERROR', format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger('admin_controller')
logger.setLevel(level='DEBUG')

file_handler_error = logging.FileHandler('logs_error.log')
file_handler_error.setLevel(level='ERROR')

file_handler_info = logging.FileHandler('logs_info.log')
file_handler_info.setLevel(level='DEBUG')

console_handler = logging.StreamHandler()
console_handler.setLevel(level='DEBUG')

logger.addHandler(file_handler_error)
logger.addHandler(file_handler_info)
logger.addHandler(console_handler)


class AdminController:

    def __init__(self, bot: Bot, user_repository_db: UserRepositoryDB,
                 check_repository_db: CheckRepositoryDB, p2p: QiwiP2P, admin: str) -> None:
        self.bot = bot
        self.user_repository_db = user_repository_db
        self.check_repository_db = check_repository_db
        self.p2p = p2p
        self.admin = admin

    async def process_admin(self, message: types.Message) -> None:
        text = 'Добро пожаловать в Админ-Панель! Выберите действие на клавиатуре'

        keyboard = types.InlineKeyboardMarkup(row_width=1)

        get_users = types.InlineKeyboardButton(text='Выгрузка пользователей с балансом', callback_data='get_users')
        get_logs = types.InlineKeyboardButton(text='Выгрузка логов', callback_data='get_logs')
        change_balance = types.InlineKeyboardButton(text='Изменить баланс пользователей',
                                                    callback_data='change_balance')
        blacklist = types.InlineKeyboardButton(text='Заблокировать пользователя', callback_data='blacklist')

        keyboard.add(get_users, get_logs, change_balance, blacklist)

        await self.bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)

    async def get_users_callback(self, call: types.CallbackQuery) -> None:
        logger.debug('Start process get_users_callback')

        text_2 = 'В БД отсутствуют пользователи'

        try:
            users = self.user_repository_db.get_users()

            for user in users:
                if user[0] != int(self.admin):
                    text_1 = f'User ID: {user[0]}\nБаланс счета: {user[1]} руб.'
                    await self.bot.send_message(call.from_user.id, text=text_1)

        except TypeError as error:
            logger.info(f'user id: {call.from_user.id}')
            logger.exception('This user was not found in the database', exc_info=error)

            await self.bot.send_message(call.from_user.id, text=text_2)

    async def blacklist_callback(self, message: types.Message) -> None:
        logger.debug('Start process blacklist_callback')

        text_1 = 'Пользователь успешно добавлен в ЧС'
        text_2 = 'Такой пользователь не найден в базе данных. Попробуйте снова, выберите команду /admin'
        text_3 = 'Вы вводите буквы!\nID состоит из цифр. Для ввода ID выберите команду /admin'

        if message.text.isdigit():
            try:
                user = self.user_repository_db.get_user(message.text)
                user.block = 1
                self.user_repository_db.set_user(user)
                await self.bot.send_message(message.from_user.id, text=text_1)

            except TypeError as error:
                logger.info(f'user id: {message.from_user.id}')
                logger.exception('This user was not found in the database', exc_info=error)

                await self.bot.send_message(message.from_user.id, text=text_2)

        else:
            await self.bot.send_message(message.from_user.id, text=text_3)

    async def reduce_money_callback(self, message: types.Message, user_id_reduce_money: str, reduce_money: str) -> None:
        user = self.user_repository_db.get_user(int(user_id_reduce_money))
        user.money -= int(reduce_money)
        self.user_repository_db.set_user(user)

        text = f'Вы уменьшили баланс пользователя ID: {user.user_id}. Теперь он составляет {user.money} руб.'

        await self.bot.send_message(message.from_user.id, text=text)

    async def get_logs_callback(self, call: types.CallbackQuery) -> None:
        with open('logs_error.log', 'rb') as doc_error, open('logs_info.log', 'rb') as doc_info:
            await self.bot.send_document(call.from_user.id, doc_error)
            await self.bot.send_document(call.from_user.id, doc_info)
