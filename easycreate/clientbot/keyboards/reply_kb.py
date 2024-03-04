from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder, KeyboardButton

from clientbot import strings
from clientbot.keyboards.functs import get_cryptomus_services
from utils.aaio.AAIO import AAIO
from config import settings


def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📲 Купить номер"),
        KeyboardButton(text="💳 Баланс"),
        KeyboardButton(text="📫 Все СМС операции"),
        KeyboardButton(text="👥 Партнёрская программа"),
        KeyboardButton(text="ℹ️ Информация"),
        width=2
    )
    return builder.as_markup(resize_keyboard=True)

def refill_crypto_balance_methods():
    builder = ReplyKeyboardBuilder()
    services = get_cryptomus_services()
    builder.row(KeyboardButton(text=strings.CANCEL), width=1)
    builder.row(*[KeyboardButton(text=f"{x.network} {x.currency}") for x in services], width=2)
    return builder.as_markup(resize_keyboard=True)

def cancel():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=strings.CANCEL)
    )
    return builder.as_markup(resize_keyboard=True)


def amount_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=strings.CANCEL), width=1)
    builder.row(
        KeyboardButton(text="50"),
        KeyboardButton(text="100"),
        KeyboardButton(text="250"),
        KeyboardButton(text="500"),
        KeyboardButton(text="1000"),
        KeyboardButton(text="5000"),
        width=3
    )
    return builder.as_markup(resize_keyboard=True)


def refill_balance_methods():
    builder = ReplyKeyboardBuilder()
    buttons = []
    # for item in LAVA_METHOD:
    #     buttons.append(
    #         KeyboardButton(text=item['name'])
    #     )
    # builder.row(*buttons, width=2)
    aaio = AAIO(settings.AAIO_ID, settings.AAIO_SECRET_1, settings.AAIO_SECRET_2, settings.AAIO_KEY)
    methods = aaio.get_payment_methods()
    for method in methods.list:
        buttons.append(
            KeyboardButton(text=method.name)
        )
    builder.row(*buttons, width=2)
    builder.row(KeyboardButton(text="Криптовалюты"), width=1)
    builder.row(KeyboardButton(text=strings.CANCEL))
    return builder.as_markup(resize_keyboard=True)
