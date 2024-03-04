from contextlib import suppress

from aiogram import types, Bot, html
from aiogram.dispatcher.filters import CommandObject
from aiogram.exceptions import TelegramBadRequest, TelegramNotFound, TelegramForbiddenError
from aiogram.types import FSInputFile

from clientbot.data.callback_datas import MainMenuCallbackData
from clientbot import strings, shortcuts
from clientbot.keyboards import inline_kb, reply_kb
from db.models import MainBotUser
from loader import client_bot_router
from config import settings
from db.models import MainBotUser

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

def get_num(text: str) -> str:
    a = text.split(":")
    b = a[1] if len(a) > 0 else a
    return b            

@client_bot_router.message(commands="start", flags={'throttling_key': 'start'})
async def start(message: types.Message, command: CommandObject):
    uid = message.from_user.id
    referral = command.args
    user = await shortcuts.get_user(uid)
    if user is None:
        if referral and referral.isdigit():
            inviter = await shortcuts.get_user(int(referral))
            if inviter:
                with suppress(TelegramBadRequest, TelegramForbiddenError):
                    await Bot.get_current().send_message(inviter.uid,
                                                         f"По вашей реф. ссылке зарегистрировался "
                                                         f"{html.link(value=str(uid), link=f'tg://user?id={uid}')}!")
                await shortcuts.reward_inviter(inviter)
        else:
            inviter = None
        await shortcuts.save_user(message.from_user, inviter)
    bot = await shortcuts.get_bot()
    if not bot.photo_is_gif:
        photo = bot.photo or FSInputFile(settings.DEFAULT_PHOTO)
        await message.answer_photo(
            photo,
            strings.WELCOME.format(name=message.from_user.first_name),
            reply_markup=reply_kb.main_menu()
        )
    else:
        await message.answer_animation(
            animation=bot.photo,
            caption=strings.WELCOME.format(name=message.from_user.first_name),
            reply_markup=reply_kb.main_menu()
        )


@client_bot_router.message(text="📲 Купить номер", flags={'throttling_key': 'buy_number'})
async def buy_number(message: types.Message):
    text = "1. Выберите страну, номер телефона которой будет Вам выдан"
    markup = await inline_kb.countries_kb()
    await message.answer(text, reply_markup=markup)
    # await message.answer(text, )


@client_bot_router.message(text="💳 Баланс", flags={'throttling_key': 'balance'})
async def balance_menu(message: types.Message):
    user = await shortcuts.get_user(message.from_user.id)
    text = strings.BALANCE.format(balance=user.balance, uid=message.from_user.id)
    await message.answer(text, reply_markup=inline_kb.balance_menu())


@client_bot_router.message(text="📫 Все СМС операции", flags={'throttling_key': 'sms_history'})
async def sms_history(message: types.Message):
    orders, count = await shortcuts.get_order_history(message.from_user.id)
    text = await strings.print_order_history(orders)
    if text is None:
        await message.answer(strings.NOTHING_FOUND)
    else:
        await message.answer(text, reply_markup=inline_kb.order_history_kb(count))


@client_bot_router.message(text="👥 Партнёрская программа", flags={'throttling_key': 'partnership'})
async def partnership(message: types.Message):
    bot = await shortcuts.get_bot()
    link = f"https://t.me/{bot.username}?start={message.from_user.id}"
    text = strings.PARTNERSHIP.format(link=link)
    await message.answer(text, reply_markup=inline_kb.partner_menu(link, ))


@client_bot_router.message(text="ℹ️ Информация", flags={'throttling_key': 'info'})
async def info(message: types.Message, bot: Bot):
    bot_obj = await shortcuts.get_bot()
    owner: MainBotUser = bot_obj.owner
    try:
        await message.answer(strings.INFO.format(username=f"@{bot_obj.username}"), reply_markup=inline_kb.info_menu(
            support=bot_obj.support or owner.uid,
            channel_link=bot_obj.news_channel
        ))
    except TelegramBadRequest as e:
        if "BUTTON_USER_INVALID" in e.message:
            await bot.send_message(owner.uid, "⚠️ Измените ид поддержки бота. Текущий недействителен.")
            await message.answer(strings.INFO.format(username=f"@{bot_obj.username}"), reply_markup=inline_kb.info_menu(
                support=owner.uid,
                channel_link=bot_obj.news_channel
            ))


@client_bot_router.callback_query(MainMenuCallbackData.filter())
async def main_menu(query: types.CallbackQuery, callback_data: MainMenuCallbackData):
    match callback_data.action:
        case None:
            try:
                await query.message.delete()
            except (TelegramBadRequest, TelegramNotFound):
                await query.message.edit_reply_markup()
            finally:
                await query.message.answer(strings.MAIN_MENU, reply_markup=reply_kb.main_menu())
