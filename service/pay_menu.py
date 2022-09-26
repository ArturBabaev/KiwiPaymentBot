from aiogram import types


def pay_menu(is_url=True, url='', bill=''):
    qiwi_menu = types.InlineKeyboardMarkup(row_width=1)
    if is_url:
        btn_url_qiwi = types.InlineKeyboardButton(text='Ссылка на оплату', url=url)
        qiwi_menu.add(btn_url_qiwi)

    btn_check_qiwi = types.InlineKeyboardButton(text='Проверить оплату', callback_data=f'check_{bill}')
    qiwi_menu.add(btn_check_qiwi)
    return qiwi_menu
