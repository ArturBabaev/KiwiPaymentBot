from aiogram import Bot, types
from pyqiwip2p import QiwiP2P
import random
from repository.user_repository import UserRepositoryDB
from repository.check_repository import CheckRepositoryDB
from model.cheque import Check
from service.pay_menu import pay_menu
# import logging
import logging.config
from logging_config import dict_config

logging.config.dictConfig(dict_config)
logger = logging.getLogger('start_controller')
logger.setLevel('DEBUG')

# logging.basicConfig(level='ERROR', format='%(asctime)s %(levelname)s:%(message)s')
# logger = logging.getLogger('start_controller')
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


class StartController:

    def __init__(self, bot: Bot, user_repository_db: UserRepositoryDB,
                 check_repository_db: CheckRepositoryDB, p2p: QiwiP2P) -> None:
        self.bot = bot
        self.user_repository_db = user_repository_db
        self.check_repository_db = check_repository_db
        self.p2p = p2p

    async def process_start(self, message: types.Message) -> None:
        if message.chat.type == 'private':
            user = self.user_repository_db.get_user(message.from_user.id)

            text = f'Привет, {user.user_name}!\nЯ - бот для пополнения баланса. ' \
                   f'Нажмите на кнопку, чтобы пополнить баланс.'

            keyboard = types.InlineKeyboardMarkup(row_width=1)

            key_top_up = types.InlineKeyboardButton(text='Пополнить баланс', callback_data='top_up')

            keyboard.add(key_top_up)

            await self.bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)

    async def top_up_callback(self, message: types.Message) -> None:
        logger.debug('Start process top_up_callback')

        if message.chat.type == 'private':
            text_1 = 'Введите целое число. Попробуйте снова, нажмите команду /start.'
            text_2 = 'Минимальная сумма для пополнения 1 руб. Попробуйте снова, нажмите команду /start.'

            try:
                message_money = int(message.text)
                if message_money >= 1:
                    comment = str(message.from_user.id) + '_' + str(random.randint(1000, 9999))
                    bill = self.p2p.bill(amount=message_money, lifetime=5, comment=comment)

                    self.check_repository_db.set_check(Check(user_id=message.from_user.id, bill_id=bill.bill_id,
                                                             money=message_money))

                    text_3 = f'Вам нужно отправить {message_money} руб. на наш счет QIWI\nСсылку: {bill.pay_url}\n' \
                             f'Указав комментарий к оплате: {comment}'

                    await self.bot.send_message(message.from_user.id, text=text_3,
                                                reply_markup=pay_menu(url=bill.pay_url, bill=bill.bill_id))

                else:
                    await self.bot.send_message(message.from_user.id, text=text_2)

            except ValueError as error:
                logger.info(f'user id: {message.from_user.id}')
                logger.exception('Money must be an integer', exc_info=error)

                await self.bot.send_message(message.from_user.id, text=text_1)

    async def check_callback(self, call: types.CallbackQuery) -> None:
        user = self.user_repository_db.get_user(call.from_user.id)
        check = self.check_repository_db.get_check(call.from_user.id)

        bill = str(call.data[6:])
        info = check.bill_id

        text_1 = 'Вы не оплатили счет!'
        text_2 = 'Счет не найден!'
        text_3 = 'Ваш счет пополнен! Нажмите /start'

        if info:
            if str(self.p2p.check(bill_id=bill).status) == 'PAID':
                money = int(check.money)
                user.money += money

                self.user_repository_db.set_user(user)

                await self.bot.send_message(call.from_user.id, text=text_3)

            else:
                await self.bot.send_message(call.from_user.id, text=text_1,
                                            reply_markup=pay_menu(is_url=False, bill=bill))

        else:
            await self.bot.send_message(call.from_user.id, text=text_2)
