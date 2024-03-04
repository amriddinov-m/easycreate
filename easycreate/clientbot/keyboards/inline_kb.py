import json
from math import ceil
from typing import Union, Optional, TYPE_CHECKING

import requests
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from smsactivate.api import SMSActivateAPI

from clientbot.data.callback_datas import (
    MainMenuCallbackData,
    BalanceCallbackData,
    CountryCallbackData,
    OperatorCallbackData,
    ProductCallbackData,
    OrderCallbackData,
    OrderHistoryCallbackData,
    BalanceHistoryCallbackData,
    AdminPanelCallbackData,
    BroadcastCallbackData,
    EditPercentCallbackData,
    MandatorySubscription
)

if TYPE_CHECKING:
    from db.models import SubscriptionChat
from clientbot import strings, shortcuts
from config import settings

cancel_button = InlineKeyboardButton(text="Отмена", callback_data="cancel")


def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📲 Купить номер", callback_data=MainMenuCallbackData(action="buy").pack()),
        InlineKeyboardButton(text="💳 Баланс", callback_data=MainMenuCallbackData(action='balance').pack()),
        InlineKeyboardButton(text="📫 Все СМС операции",
                             callback_data=MainMenuCallbackData(action="history").pack()),
        InlineKeyboardButton(text="👥 Партнёрская программа",
                             callback_data=MainMenuCallbackData(action="partner").pack()),
        InlineKeyboardButton(text="ℹ️ Информация", callback_data=MainMenuCallbackData(action="info").pack()),
        width=2
    )
    return builder.as_markup()


def info_menu(support: Union[int, str], channel_link: str = None):
    if isinstance(support, int) or support.isdigit():
        support_link = f"tg://user?id={support}"
    else:
        support_link = f"https://t.me/{support}"
    builder = InlineKeyboardBuilder()
    buttons = [InlineKeyboardButton(text="👨‍💻 Техподдержка / Администратор", url=support_link)]
    if channel_link:
        buttons.append(InlineKeyboardButton(text="📢 Новости", url=channel_link))
    builder.row(
        *buttons,
        InlineKeyboardButton(text=strings.BACK, callback_data=MainMenuCallbackData().pack()),
        width=1
    )
    return builder.as_markup()


def partner_menu(link: str):
    url = f"https://t.me/share/url?url={link}&text=Сервис для приёма SMS сообщений"
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔗 Поделиться ссылкой", url=url),
        InlineKeyboardButton(text=strings.BACK, callback_data=MainMenuCallbackData().pack()),
        width=1
    )
    return builder.as_markup()


def balance_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📈 История",
                             callback_data=BalanceCallbackData(action="history").pack()),
        InlineKeyboardButton(text="💰 Пополнить баланс",
                             callback_data=BalanceCallbackData(action="refill").pack()),
        InlineKeyboardButton(text=strings.BACK, callback_data=MainMenuCallbackData().pack()),
        width=1
    )
    return builder.as_markup()


async def countries_kb(page: int = 1, search_key: str = None):
    countries, length = await shortcuts.get_countries(page, search_key=search_key)
    builder = InlineKeyboardBuilder()
    buttons = []
    for country in countries:
        country_code = country['code']
        buttons.append(
            InlineKeyboardButton(text=country['name'],
                                 callback_data=CountryCallbackData(action="retrieve", country_code=country_code,
                                                                   country=country['name'], page=page).pack())
        )
    builder.row(*buttons, width=3)
    pagination_row = []
    pages = ceil(length / 15)
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️",
                                 callback_data=CountryCallbackData(action="paginate", country_code=country_code,
                                                                   country="-1", page=page - 1).pack())
        )
    pagination_row.append(
        InlineKeyboardButton(text=f"Стр: {page} из {pages}",
                             callback_data=CountryCallbackData(action="page-list", country_code=country_code,
                                                               country="-1", page=page).pack())
    )
    if page < pages:
        pagination_row.append(
            InlineKeyboardButton(text="➡️", callback_data=CountryCallbackData(action="paginate",
                                                                              country_code=country_code, country="-1",
                                                                              page=page + 1).pack())
        )
    builder.row(*pagination_row, width=3)
    builder.row(
        InlineKeyboardButton(text=strings.BACK, callback_data=MainMenuCallbackData().pack())
    )
    return builder.as_markup()


async def countries_pages_kb(page: int = 1):
    builder = InlineKeyboardBuilder()
    _, length = await shortcuts.get_countries()
    pages = ceil(length / 15)
    buttons = []
    for i in range(1, pages + 1):
        buttons.append(
            InlineKeyboardButton(text=f"-{i}-" if i == page else str(i),
                                 callback_data=CountryCallbackData(action="paginate", country_code="-1", page=i).pack())
        )
    builder.row(*buttons, width=6)
    builder.row(
        InlineKeyboardButton(text=strings.BACK,
                             callback_data=CountryCallbackData(action="paginate", country_code="-1", page=page).pack()),
        width=1
    )
    return builder.as_markup()


async def operators_kb(country_code: str):
    builder = InlineKeyboardBuilder()
    buttons = []
    response = requests.get(
        f'{settings.SMS_ACTIVATE_URL}getTariffs.php?apikey={settings.SMS_ACTIVATE_TOKEN}&filter_country={country_code}').json()
    print('START')
    print(response['services'])

    with open("operators.json", "w") as file:
        file.write(json.dumps(response))
    if response["response"] == "1":
        # res = response["countryOperators"]
        # res = res[0] if isinstance(res, list) else res[country_code]
        for key in response['services']:
            print(response['services'][key]['service'])
            operator = response['services'][key]
            buttons.append(
                InlineKeyboardButton(text=f"{operator['service']} - {operator['price']}р",
                                     callback_data=OperatorCallbackData(country_code=country_code,
                                                                        operator=operator['slug']).pack())
            )
    builder.row(*buttons, width=2)
    builder.row(InlineKeyboardButton(text=strings.BACK,
                                     callback_data=CountryCallbackData(action="paginate", country_code=country_code,
                                                                       page=1).pack()))
    return builder.as_markup()


async def products_kb(country_code: str, operator: str, page: int = 1):
    builder = InlineKeyboardBuilder()
    buttons = []
    try:
        products, length = await shortcuts.get_products(country_code, operator, page)
    except Exception as e:
        raise e

    for product in products:
        product: dict = product
        with open("product.json", "w") as file:
            file.write(json.dumps(product))
        key = list(product.keys())[0]
        if key in strings.SERVICES:
            count = product[key]['quant']['current']
            product_name = f"{strings.SERVICES[key]['name']} ({count})"
            buttons.append(
                InlineKeyboardButton(text=f"{product_name}",
                                     callback_data=ProductCallbackData(action="retrieve",
                                                                       country_code=country_code,
                                                                       operator=operator,
                                                                       product=key).pack())
            )
    builder.row(*buttons, width=3)
    pagination_row = []
    pages = ceil(length / 15)
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️", callback_data=ProductCallbackData(action="paginate",
                                                                              country_code=country_code,
                                                                              operator=operator,
                                                                              product="-1",
                                                                              page=page - 1).pack())
        )
    pagination_row.append(
        InlineKeyboardButton(text=f"Стр: {page} из {pages}",
                             callback_data=ProductCallbackData(action="page-list",
                                                               country_code=country_code,
                                                               operator=operator,
                                                               product="-1",
                                                               page=page).pack())
    )
    if page < pages:
        pagination_row.append(
            InlineKeyboardButton(text="➡️", callback_data=ProductCallbackData(action="paginate",
                                                                              country_code=country_code,
                                                                              operator=operator,
                                                                              product="-1",
                                                                              page=page + 1).pack())
        )
    builder.row(*pagination_row, width=3)
    builder.row(
        InlineKeyboardButton(text=strings.BACK,
                             callback_data=CountryCallbackData(action="retrieve", page=1,
                                                               country_code=country_code).pack()),
        width=1
    )
    return builder.as_markup()


async def products_pages_kb(callback_data: ProductCallbackData):
    _, length = await shortcuts.get_products(callback_data.country_code, callback_data.operator, callback_data.page)
    builder = InlineKeyboardBuilder()
    pages = ceil(length / 15)
    buttons = []
    for i in range(1, pages + 1):
        buttons.append(
            InlineKeyboardButton(text=f"-{i}!-" if i == callback_data.page else str(i),
                                 callback_data=ProductCallbackData(
                                     country_code=callback_data.country_code,
                                     product=callback_data.product,
                                     operator=callback_data.operator,
                                     action="paginate", page=i).pack())
        )
    builder.row(*buttons, width=6)
    builder.row(
        InlineKeyboardButton(text=strings.BACK,
                             callback_data=ProductCallbackData(country_code=callback_data.country_code,
                                                               product=callback_data.product,
                                                               operator=callback_data.operator, action="paginate",
                                                               page=callback_data.page).pack()),
        width=1
    )
    return builder.as_markup()


def buy_product_kb(country_code: str, operator: str, product: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Купить",
                             callback_data=ProductCallbackData(
                                 action="buy",
                                 country_code=country_code,
                                 operator=operator,
                                 product=product,
                                 page=1
                             ).pack()),
        InlineKeyboardButton(text=strings.BACK,
                             callback_data=ProductCallbackData(
                                 action="paginate",
                                 country_code=country_code,
                                 operator=operator,
                                 product=product,
                                 page=1
                             ).pack()),
        width=1
    )
    return builder.as_markup()


def back_kb(callback_data: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=strings.BACK, callback_data=callback_data)
    )
    return builder.as_markup()


def order_actions(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Проверить",
                             callback_data=OrderCallbackData(action="check", order_id=order_id).pack()),
        InlineKeyboardButton(text="Изменить номер",
                             callback_data=OrderCallbackData(action="change", order_id=order_id).pack()),
        InlineKeyboardButton(text="Отменить",
                             callback_data=OrderCallbackData(action="cancel", order_id=order_id).pack()),
        InlineKeyboardButton(text="Бан",
                             callback_data=OrderCallbackData(action="ban", order_id=order_id).pack()),
        width=2
    )
    return builder.as_markup()


def order_history_kb(length: int, page: int = 1):
    pages = ceil(length / settings.HISTORY_LIMIT)
    buttons = []
    builder = InlineKeyboardBuilder()
    if page > 1:
        buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=OrderHistoryCallbackData(page=page - 1).pack())
        )
    buttons.append(
        InlineKeyboardButton(text=f"Стр. {page} из {pages}",
                             callback_data=OrderHistoryCallbackData(action="page-list", page=page).pack())
    )
    if page < pages:
        buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=OrderHistoryCallbackData(page=page + 1).pack())
        )
    builder.row(*buttons, width=3)
    return builder.as_markup()


def order_history_pages(length: int, page: int = 1):
    pages = ceil(length / settings.HISTORY_LIMIT)
    buttons = []
    builder = InlineKeyboardBuilder()
    for i in range(1, pages + 1):
        buttons.append(
            InlineKeyboardButton(text=f"-{i}-" if i == page else str(i),
                                 callback_data=OrderHistoryCallbackData(page=i).pack())
        )
    builder.row(*buttons, width=8)
    builder.row(
        InlineKeyboardButton(text=strings.BACK, callback_data=OrderHistoryCallbackData(page=page).pack()),
        width=1
    )
    return builder.as_markup()


def balance_history_kb(length: int, page: int = 1):
    pages = ceil(length / settings.HISTORY_LIMIT)
    buttons = []
    builder = InlineKeyboardBuilder()
    if page > 1:
        buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=BalanceHistoryCallbackData(page=page - 1).pack())
        )
    buttons.append(
        InlineKeyboardButton(text=f"Стр. {page} из {pages}",
                             callback_data=BalanceHistoryCallbackData(action="page-list", page=page).pack())
    )
    if page < pages:
        buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=BalanceHistoryCallbackData(page=page + 1).pack())
        )
    builder.row(*buttons, width=3)
    builder.row(
        InlineKeyboardButton(text=strings.BACK, callback_data=BalanceHistoryCallbackData(action="back").pack()),
        width=1
    )
    return builder.as_markup()


def balance_history_pages(length: int, page: int = 1):
    pages = ceil(length / settings.HISTORY_LIMIT)
    buttons = []
    builder = InlineKeyboardBuilder()
    for i in range(1, pages + 1):
        buttons.append(
            InlineKeyboardButton(text=f"-{i}-" if i == page else str(i),
                                 callback_data=BalanceHistoryCallbackData(page=i).pack())
        )
    builder.row(*buttons, width=8)
    builder.row(
        InlineKeyboardButton(text=strings.BACK, callback_data=BalanceHistoryCallbackData(page=page).pack()),
        width=1
    )
    return builder.as_markup()


def payment(url: str, order_id: str):
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(text="Оплатить", url=url),
        cancel_button,
    ]
    builder.row(*buttons, width=1)
    return builder.as_markup()


def admin_buttons():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data=AdminPanelCallbackData(action="statistics").pack()),
        InlineKeyboardButton(text="✉️ Рассылка", callback_data=AdminPanelCallbackData(action="broadcast").pack()),
        InlineKeyboardButton(text="📄 Обязательная подписка",
                             callback_data=AdminPanelCallbackData(action="mandatory-subscription").pack()),
        InlineKeyboardButton(text="🖼 Сменить фото",
                             callback_data=AdminPanelCallbackData(action="change-photo").pack()),
        InlineKeyboardButton(text="📢 Изменить новостной канал",
                             callback_data=AdminPanelCallbackData(action="channel-link").pack()),
        InlineKeyboardButton(text="⚖️ Изменить процент",
                             callback_data=AdminPanelCallbackData(action="change-percent").pack()),
        InlineKeyboardButton(text="👨‍💻 Изменить username поддержки",
                             callback_data=AdminPanelCallbackData(action="change-support").pack()),
        InlineKeyboardButton(text="💸 Продать бота",
                             callback_data=AdminPanelCallbackData(action="change-admin").pack()),
        InlineKeyboardButton(text="📤 Дамп пользователей",
                             callback_data=AdminPanelCallbackData(action="dump-users").pack()),
        InlineKeyboardButton(text="📥 Импорт пользователей",
                             callback_data=AdminPanelCallbackData(action="import-users").pack()),

        width=1

    )
    return builder.as_markup()


def back_to_admin_panel():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=strings.BACK, callback_data=AdminPanelCallbackData().pack())
    )
    return builder.as_markup()


def admin_panel_cancel():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=strings.BACK, callback_data=AdminPanelCallbackData(action="cancel").pack())
    )
    return builder.as_markup()


def broadcast_confirmation():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Да",
                             callback_data=BroadcastCallbackData(action="confirmation", confirm=True).pack()),
        InlineKeyboardButton(text=strings.CANCEL,
                             callback_data=BroadcastCallbackData(action="confirmation", confirm=False).pack()),
        width=1
    )
    return builder.as_markup()


def switch_broadcast_status(paused=False):
    if paused:
        text = "⏯ Продолжить"
    else:
        text = "⏯ Пауза"
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=text, callback_data=BroadcastCallbackData(action="switch").pack()),
        InlineKeyboardButton(text="🔄 Обновить", callback_data=BroadcastCallbackData(action="update").pack()),
        InlineKeyboardButton(text="⏹ Остановить", callback_data=BroadcastCallbackData(action="stop").pack()),
        width=1
    )
    return builder.as_markup()


def percents():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="30%", callback_data=EditPercentCallbackData(percent=30).pack()),
        InlineKeyboardButton(text="40%", callback_data=EditPercentCallbackData(percent=40).pack()),
        InlineKeyboardButton(text="50%", callback_data=EditPercentCallbackData(percent=50).pack()),
        InlineKeyboardButton(text="60%", callback_data=EditPercentCallbackData(percent=60).pack()),
        InlineKeyboardButton(text="70%", callback_data=EditPercentCallbackData(percent=70).pack()),
        width=3
    )
    builder.row(
        InlineKeyboardButton(text=strings.BACK, callback_data=AdminPanelCallbackData().pack())
    )
    return builder.as_markup()


def post_buttons(reply_markup: Optional[InlineKeyboardMarkup] = None):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Send", callback_data=BroadcastCallbackData(action="send").pack()),
        InlineKeyboardButton(text="Добавить кнопку", callback_data=BroadcastCallbackData(action="add-button").pack()),
        width=1
    )
    if reply_markup:
        buttons = []
        for row in reply_markup.inline_keyboard:
            for button in row:
                if button.url:
                    buttons.append(button)
        if buttons:
            builder.row(*buttons, width=len(buttons))
    return builder.as_markup()


def add_buttons_to_post(markup: InlineKeyboardMarkup, buttons: list[tuple]):
    builder = InlineKeyboardBuilder(markup=markup.inline_keyboard)
    builder.row(*[InlineKeyboardButton(text=text, url=url) for text, url in buttons], width=len(buttons))
    return builder.as_markup()


def remove_buttons_from_post(reply_markup: Optional[InlineKeyboardMarkup] = None):
    if reply_markup:
        keyboards = reply_markup.inline_keyboard
        builder = InlineKeyboardBuilder()
        for row in keyboards:
            buttons = []
            for button in row:
                if button.url:
                    buttons.append(button)
            if buttons:
                builder.row(*buttons, width=len(buttons))
        return builder.as_markup()


def mandatory_subscription_status(is_turned_on: bool, chats_count: int = 0):
    builder = InlineKeyboardBuilder()
    btn_txt = "Выключить" if is_turned_on else "Включить"
    builder.row(
        InlineKeyboardButton(text=btn_txt,
                             callback_data=MandatorySubscription(action="switch").pack()),
        width=1
    )
    action_buttons = [
        InlineKeyboardButton(text="➕ Добавить чат", callback_data=MandatorySubscription(action="add").pack())
    ]
    if chats_count:
        action_buttons.append(
            InlineKeyboardButton(text="🗑 Удалить чат", callback_data=MandatorySubscription(action="remove").pack())
        )
    builder.row(*action_buttons, width=len(action_buttons))
    builder.row(
        InlineKeyboardButton(text=strings.BACK, callback_data=MandatorySubscription().pack()),
        width=1
    )
    return builder.as_markup()


def choose_subscription_chat(chats: list["SubscriptionChat"]):
    builder = InlineKeyboardBuilder()
    buttons = []
    for idx, chat in enumerate(chats, 1):
        buttons.append(
            InlineKeyboardButton(text=str(idx),
                                 callback_data=MandatorySubscription(action="choose-to-remove", id=chat.uid).pack())
        )
    builder.row(*buttons, width=8)
    builder.row(
        InlineKeyboardButton(text=strings.BACK, callback_data=MandatorySubscription(action="choose-to-remove").pack()),
        width=1
    )
    return builder.as_markup()
