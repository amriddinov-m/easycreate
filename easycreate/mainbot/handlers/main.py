from aiogram import types, F, Bot, flags
from aiogram.dispatcher.filters import CommandObject

from config import settings
from loader import main_bot_router
from mainbot import shortcuts, strings
from mainbot.keyboards import inline_kb, reply_kb


@main_bot_router.message(commands="start", state="*", flags={"throttling_key": "start"})
async def start(message: types.Message, command: CommandObject):
    new_user = False
    uid = message.from_user.id
    user = await shortcuts.get_user(uid)
    if not user:
        new_user = True
        await shortcuts.save_user(message.from_user)
    if uid not in settings.ADMIN_LIST:
        referral = command.args
        if referral and referral.isdigit():
            if new_user:
                await shortcuts.increase_referral(int(referral))
    await message.answer(strings.WELCOME, reply_markup=reply_kb.main_menu())


@main_bot_router.message(text="📬 Мой кабинет")
@flags.rate_limit(key="user_cabinet")
async def user_cabinet(message: types.Message):
    user = await shortcuts.get_user(message.from_user.id)
    frozen_balance = await shortcuts.get_frozen_balance(user)
    if not user:
        user = await shortcuts.save_user(message.from_user)
    bot_ = await shortcuts.get_user_bot(message.from_user.id)
    text = strings.CABINET_INFO.format(
        uid=message.from_user.id,
        balance=f"{user.balance:.2f}",
        bots=1 if bot_ else 0,
        bot_username=f"@{bot_.username}" if bot_ else "",
        percent=f"\nВаша процентная ставка: {bot_.percent}%" if bot_ else ""
    )
    #        frozen_balance=f"{frozen_balance:.2f}",
    await message.answer(text, reply_markup=inline_kb.my_cabinet())


@main_bot_router.message(F.chat.id.in_(settings.ADMIN_LIST), commands="admin")
@flags.rate_limit(key="control")
async def control(message: types.Message):
    await message.answer("📁 Выберите подходящий пункт меню", reply_markup=inline_kb.control_panel())


@main_bot_router.message(text="❓ FAQ")
@flags.rate_limit(key="faq")
async def faq(message: types.Message):
    await message.answer(strings.FAQ)


@main_bot_router.message(text="👥 Партнёры")
@flags.rate_limit(key="partners")
async def partners(message: types.Message):
    uid = message.from_user.id
    user = await shortcuts.get_user(uid)
    bot_ = await Bot.get_current().me()
    if not user:
        user = await shortcuts.save_user(message.from_user)
    text = strings.PARTNERS.format(
        user.referral_count,
        user.referral_balance,
        bot_.username,
        uid
    )
    await message.answer(text, reply_markup=inline_kb.transfer())


@main_bot_router.message(text="ℹ️ Информация")
@flags.rate_limit(key="info")
async def info(message: types.Message):
    user = await shortcuts.get_user(message.from_user.id)
    if not user:
        await shortcuts.save_user(message.from_user)
    await message.answer(
        text="📒 Информация: ",
        reply_markup=inline_kb.info()
    )


@main_bot_router.message(text="🤖 Создать бота")
@flags.rate_limit(key="create_bot")
async def create_bot(message: types.Message):
    user = await shortcuts.get_user(message.from_user.id)
    if not user:
        await shortcuts.save_user(message.from_user)
    user_bot = await shortcuts.get_user_bot(message.from_user.id)
    if user_bot:
        await message.answer("⛔️ Вы уже создавали бота!")
        return
    await message.answer(strings.CHOOSE_PERCENT, reply_markup=inline_kb.percents())
