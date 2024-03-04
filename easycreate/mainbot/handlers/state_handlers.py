from aiogram import types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import TelegramUnauthorizedError, TelegramBadRequest, TelegramForbiddenError
from aiogram.utils.token import TokenValidationError

from config import settings
from loader import main_bot_router, bot_session, main_bot
from mainbot import strings, shortcuts
from mainbot.data import states
from mainbot.keyboards import reply_kb, inline_kb


@main_bot_router.message(state=states.NewBot.token)
async def create_bot(message: types.Message, state: FSMContext):
    try:
        token = message.text
        url = settings.WEBHOOK_URL.format(token=token)
        async with Bot(token, session=bot_session).context(auto_close=False) as bot:
            msg = await main_bot.send_message(message.from_user.id, "💾 Пожалуйста подождите ваш бот создаётся")
            await bot.set_webhook(url, allowed_updates=settings.USED_UPDATE_TYPES)
            await bot.set_my_commands(
                [types.BotCommand(command="start", description="Главное меню")]
            )
            bot_me = await bot.get_me()
        data = await state.get_data()
        await shortcuts.save_bot(token, message.from_user.id, data.get('percent'), bot_me.username)
        try:
            await main_bot.delete_message(msg.chat.id, msg.message_id)
        except TelegramBadRequest:
            pass
        await main_bot.send_message(
            msg.chat.id,
            f"🤖 Бот @{bot_me.username} успешно создан и запущен",
            reply_markup=reply_kb.main_menu()
        )

        await state.clear()

    except (TokenValidationError, TelegramUnauthorizedError, TypeError):
        await message.answer(
            text="⛔️ Неверный токен, пожалуйста попробуйте ввести другой токен и повторите попытку",
        )
    except Exception as e:
        try:
            bot = Bot.get_current()
            for chat_id in settings.ADMIN_LIST:
                await bot.send_message(chat_id, str(e))
        except (TelegramBadRequest, TelegramForbiddenError):
            pass
        raise e


# Broadcasting
@main_bot_router.message(state=states.Broadcast.message)
async def broadcast(message: types.Message, state: FSMContext):
    await message.answer("Сообщение готово к отправке", reply_markup=reply_kb.main_menu())
    if message.text == "*":
        await state.update_data(message="*", admin_uid=message.from_user.id)
    else:
        await state.update_data(message=message.json(exclude_none=True), admin_uid=message.from_user.id)
    await state.set_state(states.Broadcast.confirmation)
    await message.answer(strings.START_BROADCASTING, reply_markup=inline_kb.broadcast_confirmation())


# Transfer money from ref to balance
@main_bot_router.message(state=states.Transfer.amount)
async def transfer_money(message: types.Message, state: FSMContext):
    if not shortcuts.validate_amount(message.text):
        await message.answer(strings.NOT_DIGIT)
        return
    amount = int(message.text)
    referral_balance = await shortcuts.referral_balance(message.from_user.id)
    if amount > referral_balance:
        await message.answer("⛔️ Недостаточно средств для снятия такой суммы денег")
        return
    await shortcuts.transfer_money(message.from_user.id, amount)
    await message.answer(strings.TRANSFER_SUCCEEDED.format(amount),
                         reply_markup=reply_kb.main_menu())
    await state.clear()


@main_bot_router.message(states.ChangeUserBalance())
async def change_user_balance(message: types.Message, state: FSMContext):
    state_ = await state.get_state()
    data = await state.get_data()
    if state_ == states.ChangeUserBalance.bot_username.state:
        bot_username = message.text
        if "@" in bot_username:
            bot_username = bot_username.replace("@", "")
        bot = await shortcuts.get_bot_by_username(bot_username)
        if bot:
            await message.answer("Введите ид пользователя")
            await state.set_state(states.ChangeUserBalance.uid)
            await state.update_data(bot_id=bot.id)
        else:
            await message.answer("Неверное юзернейм бота")
    elif state_ == states.ChangeUserBalance.uid.state:
        try:
            uid = int(message.text)
            if not await shortcuts.get_bot_user(data.get('bot_id'), uid):
                raise ValueError
            await state.update_data(uid=uid)
            await message.answer("Введите сумму")
            await state.set_state(states.ChangeUserBalance.sum)
        except ValueError:
            await message.answer(strings.USER_NOT_FOUND)
    elif state_ == states.ChangeUserBalance.sum.state:
        try:
            bot = await shortcuts.get_bot(id=data.get('bot_id'))
            user = await shortcuts.get_bot_user(data.get('bot_id'), data.get("uid"))
            if user:
                amount = float(message.text)
                user = await shortcuts.change_balance(user, amount, "charge", "admin")
                await message.answer(f"Баланс пользователя обновлен. Текущий баланс: {user.balance:.2f}",
                                     reply_markup=reply_kb.main_menu())
                async with Bot(token=bot.token, session=bot_session).context(auto_close=False) as b:
                    await b.send_message(
                        user.uid,
                        f"🎊 Ваш баланс успешно пополнен на {amount:.2f} ₽"
                    )
            else:
                await message.answer(strings.USER_NOT_FOUND)
        except ValueError:
            await message.answer("Неверная сумма")
        finally:
            await state.clear()
