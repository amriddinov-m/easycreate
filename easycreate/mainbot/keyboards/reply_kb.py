from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from mainbot import strings
from config import settings
from utils.aaio.AAIO import AAIO


def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(*[KeyboardButton(text=i) for i in strings.MAIN_MENU_BUTTONS], width=2)
    return builder.as_markup(resize_keyboard=True)


def cancel():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Отмена"))
    return builder.as_markup(resize_keyboard=True)


def fowpay_payout_methods():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=strings.CANCEL), width=1)
    buttons = []
    # for value in LAVA_METHOD:
    #     buttons.append(
    #         KeyboardButton(text=value['name'])
    #     )
    aaio = AAIO(settings.AAIO_ID, settings.AAIO_SECRET_1, settings.AAIO_SECRET_2, settings.AAIO_KEY)
    methods = aaio.get_payout_methods()
    for method in methods.list:
        buttons.append(
            KeyboardButton(text=method.name)
        )    
    builder.row(*buttons, width=2)
    return builder.as_markup(resize_keyboard=True)


def withdraw_confirmation():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Перевести"),
        KeyboardButton(text=strings.CANCEL),
        width=1
    )
    return builder.as_markup(resize_keyboard=True)
