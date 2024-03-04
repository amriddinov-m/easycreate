from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from mainbot import strings
from mainbot.data import callback_datas


def my_cabinet():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💸Вывести деньги", callback_data="payout"),
        InlineKeyboardButton(text="📝Изменить процентую ставку", callback_data="edit_percent"),
        InlineKeyboardButton(text="❌Удалить бота", callback_data=callback_datas.ControlBot(action="delete").pack()),
        InlineKeyboardButton(text="Отмена", callback_data="cancel"),
        width=1
    )
    return builder.as_markup()


def delete_bot_confirmation():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Да",
                             callback_data=callback_datas.ControlBot(action='confirmation', confirm=True).pack()),
        InlineKeyboardButton(text="Отмена",
                             callback_data=callback_datas.ControlBot(action="confirmation", confirm=False).pack()),
        width=1
    )
    return builder.as_markup()


def cancel():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    return builder.as_markup()

def admin_yes_no(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Подтвердить", callback_data=callback_datas.AdminYesNo(action="accept", payout_id=order_id).pack()))
    builder.row(InlineKeyboardButton(text="Отмена", callback_data=callback_datas.AdminYesNo(action="cancel", payout_id=order_id).pack()))
    return builder.as_markup()


def control_panel():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Рассылка", callback_data=callback_datas.ControlPanel(action="broadcast").pack()),
        InlineKeyboardButton(text="Статистика", callback_data=callback_datas.ControlPanel(action="statistic").pack()),
        InlineKeyboardButton(text="Изменить баланс пользователя",
                             callback_data=callback_datas.ControlPanel(action="change-balance").pack()),
        InlineKeyboardButton(text="Перезапуск ботов",
                             callback_data=callback_datas.ControlPanel(action="restart-bots").pack()),
        InlineKeyboardButton(text="Отмена", callback_data="cancel"),
        width=1
    )
    return builder.as_markup()


def broadcast_confirmation():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Отправить всем пользователям",
                             callback_data=callback_datas.Broadcast(confirm=True, to_all=True).pack()),
        InlineKeyboardButton(text="Отправить пользователям основного бота",
                             callback_data=callback_datas.Broadcast(confirm=True).pack()),
        InlineKeyboardButton(text=strings.CANCEL, callback_data=callback_datas.Broadcast(confirm=False).pack()),
        width=1
    )
    return builder.as_markup()


def info():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👮‍♂️ Техподдержка / Администратор", url="t.me/DavirovS"),
        InlineKeyboardButton(text="🗞 Новости", url="https://t.me/easycreatenovosti"),
        InlineKeyboardButton(text="💵 Выплаты", url="https://t.me/easycreateviplati"),
        width=1
    )
    return builder.as_markup()


def percents(edit: bool = False):
    callback_data_class = callback_datas.ChoosePercent if not edit else callback_datas.EditPercent
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="30%", callback_data=callback_data_class(percent=30).pack()),
        InlineKeyboardButton(text="40%", callback_data=callback_data_class(percent=40).pack()),
        InlineKeyboardButton(text="50%", callback_data=callback_data_class(percent=50).pack()),
        InlineKeyboardButton(text="60%", callback_data=callback_data_class(percent=60).pack()),
        InlineKeyboardButton(text="70%", callback_data=callback_data_class(percent=70).pack()),
        width=3
    )
    builder.row(
        InlineKeyboardButton(text="Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def transfer():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰Перевести деньги на баланс",
                             callback_data=callback_datas.Transfer().pack())
    )
    return builder.as_markup()


def send_delete_request(uid: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Удалить бота",
                             callback_data=callback_datas.DeleteBotRequest(action="confirm", bot_admin=uid).pack()),
        InlineKeyboardButton(text="Отмена",
                             callback_data=callback_datas.DeleteBotRequest(action="cancel", bot_admin=uid).pack())
    )
    return builder.as_markup()
