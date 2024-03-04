import asyncio
import json
import logging
from asyncio import get_event_loop
from contextlib import suppress
# from py_lava_api.LavaAPI import LavaAPI
from aiogram import types, Bot, html, flags
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest, TelegramUnauthorizedError, TelegramForbiddenError
from aiogram.methods import SendChatAction

from config import settings
from db import models
from loader import main_bot_router, main_bot, bot_session
from mainbot import strings, shortcuts
from mainbot.data import callback_datas, states
from mainbot.keyboards import inline_kb, reply_kb

logger = logging.getLogger()


@main_bot_router.callback_query(text="cancel")
@flags.rate_limit(key="cancel")
async def cancel(query: types.CallbackQuery):
    with suppress(TelegramBadRequest):
        await query.answer()
        await query.message.delete()


@main_bot_router.callback_query(callback_datas.ChoosePercent.filter())
@flags.rate_limit(key="choose_percent")
async def choose_percent(query: types.CallbackQuery, state: FSMContext, callback_data: callback_datas.ChoosePercent):
    with suppress(TelegramBadRequest):
        await query.message.delete()
    await state.update_data(percent=callback_data.percent)
    await query.message.answer(strings.SEND_TOKEN, reply_markup=reply_kb.cancel(), disable_web_page_preview=True)
    await state.set_state(states.NewBot.token)


@main_bot_router.callback_query(callback_datas.EditPercent.filter())
@flags.rate_limit(key="edit_percent")
async def edit_percent(query: types.CallbackQuery, callback_data: callback_datas.EditPercent):
    await shortcuts.edit_bot_percent(query.from_user.id, callback_data.percent)
    await query.message.edit_text(text="✅ Успешно изменено")


@main_bot_router.callback_query(text="edit_percent")
@flags.rate_limit(key="edit_percent")
async def edit_percent(query: types.CallbackQuery):
    bot = await shortcuts.get_user_bot(query.from_user.id)
    if not bot:
        await query.answer("У тебя нет бота.")
        await query.message.delete()
    else:
        await query.message.edit_text(
            text="Выберите новую процентную ставку",
            reply_markup=inline_kb.percents(edit=True)
        )


@main_bot_router.callback_query(callback_datas.ControlPanel.filter(), flags={"throttling_key": "control_panel"})
async def control_panel(query: types.CallbackQuery, state: FSMContext, callback_data: callback_datas.ControlPanel):
    await query.answer()
    if callback_data.action == "broadcast":
        try:
            await query.message.delete()
        except TelegramBadRequest:
            pass
        users_count = await shortcuts.users_count()
        await query.message.answer((strings.BROADCAST.format(int(users_count * settings.SLEEP_TIME))),
                                   reply_markup=reply_kb.cancel())
        await state.set_state(states.Broadcast.message)
    elif callback_data.action == "statistic":
        users = await shortcuts.get_all_users_count()
        main_bot_users = await shortcuts.users_count()
        bots = await shortcuts.bots_count()
        new_users = await shortcuts.new_users()
        ordered_today = await shortcuts.ordered_today()
        earned_today = await shortcuts.earned_today()
        earned = await shortcuts.earned()
        text = strings.STATISTICS.format(
            users=users,
            main_bot_users=main_bot_users,
            bots=bots,
            new_users=new_users,
            earned=earned,
            earned_today=earned_today,
            orders_today=ordered_today,
        )
        await query.message.edit_text(text, reply_markup=inline_kb.cancel())
    elif callback_data.action == "restart-bots":
        await query.message.edit_text("Этот процесс может занять много времени")
        loop = get_event_loop()
        loop.create_task(shortcuts.restart_bots(query.from_user.id))
    elif callback_data.action == "change-balance":
        try:
            await query.message.delete()
        except TelegramBadRequest:
            pass
        await query.message.answer("Введите юзернейм бота", reply_markup=reply_kb.cancel())
        await state.set_state(states.ChangeUserBalance.bot_username)


async def broadcast_to_users(data: dict, to_all: bool = False):
    admin_uid = data.get("admin_uid")
    errors = {}
    if data.get('message') == "*":
        method = SendChatAction
        kwargs = {"action": "typing"}
    else:
        kwargs = {}
        method = types.Message(**json.loads(data.get('message'))).send_copy
    succeed, failed = 0, 0
    if not to_all:
        users = await shortcuts.get_bot_users()
        for user in users:
            if user.uid in settings.ADMIN_LIST:
                continue
            try:
                kwargs.update(chat_id=user.uid)
                await main_bot(method(**kwargs))
                succeed += 1
                await asyncio.sleep(settings.SLEEP_TIME)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except Exception as e:
                if e not in errors:
                    errors[e] = 1
                else:
                    errors[e] += 1
                failed += 1
    else:
        for bot_model in await shortcuts.get_bots():
            async with Bot(token=bot_model.token, session=bot_session).context(auto_close=False) as bot:
                try:
                    await bot.me()
                except TelegramUnauthorizedError:
                    bot_model.unauthorized = True
                    await bot_model.save()
                    continue
                clients = await bot_model.clients.all()
                for user in clients:
                    try:
                        if user.uid in settings.ADMIN_LIST or user.uid == bot_model.owner.uid:
                            continue
                        kwargs.update(chat_id=user.uid)
                        await bot(method(**kwargs))
                        succeed += 1
                        await asyncio.sleep(settings.SLEEP_TIME)
                    except TelegramRetryAfter as e:
                        await asyncio.sleep(e.retry_after)
                    except Exception as e:
                        if e not in errors:
                            errors[e] = 1
                        else:
                            errors[e] += 1
                        logger.error(e)
                        failed += 1
    await main_bot.send_message(admin_uid, strings.BROADCAST_RESULT.format(succeed, failed))


@main_bot_router.callback_query(callback_datas.Broadcast.filter(), state=states.Broadcast.confirmation)
@flags.rate_limit(key="broadcast_confirmation")
async def broadcast_confirmation(query: types.CallbackQuery, callback_data: callback_datas.Broadcast,
                                 state: FSMContext):
    if callback_data.confirm:
        await query.message.edit_text(strings.WAIT)
        data = await state.get_data()
        await broadcast_to_users(data, callback_data.to_all)
        await state.clear()
    else:
        await query.message.edit_text(strings.CANCELLED)
        
        
@main_bot_router.callback_query(callback_datas.AdminYesNo.filter())
@flags.rate_limit(key="broadcast_confirmation")
async def broadcast_confirmation(query: types.CallbackQuery, callback_data: callback_datas.AdminYesNo,
                                 state: FSMContext):
    payout = await shortcuts.get_payout_id(callback_data.payout_id)
    await query.message.delete()
    if callback_data.action == "accept":
        # lava = LavaAPI(settings.LAVA_SHOP_ID, settings.LAVA_KEY_SECRET, settings.LAVA_KEY_STILL, payout_webhook=f"{settings.HOST}/client-bot/payouts/lava")
        # lava.generate_payout(payout.payout_amount, payout.payout_id, payout.payout_wallet_type, payout.payout_wallet)
        return
    
    user: models.MainBotUser = await payout.user
    await main_bot.send_message(user.uid, "К сожалению, админ отклонил вашу заявку на вывод. Попробуйте позже.")
        


@main_bot_router.callback_query(callback_datas.Broadcast.filter())
@flags.rate_limit(key="cancel_broadcasting")
async def cancel_broadcasting(query: types.CallbackQuery):
    await query.answer("Это действие недопустимо.")
    try:
        await query.message.delete()
    except TelegramBadRequest:
        await query.message.edit_reply_markup()


@main_bot_router.callback_query(callback_datas.Transfer.filter())
@flags.rate_limit(key="transfer")
async def transfer(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass
    referral_balance = await shortcuts.referral_balance(query.from_user.id)
    if referral_balance <= 0:
        await query.message.answer(strings.NOT_ENOUGH_MONEY)
        return
    await query.message.answer(strings.TRANSFER_INFO.format(referral_balance), reply_markup=reply_kb.cancel())
    await state.set_state(states.Transfer.amount)


# Delete the bot
@main_bot_router.callback_query(callback_datas.ControlBot.filter())
async def delete_the_bot(query: types.CallbackQuery, callback_data: callback_datas.ControlBot):
    bot_in_db = await shortcuts.get_user_bot(query.from_user.id)
    if callback_data.action == "delete":
        if bot_in_db:
            await query.message.edit_text("Вы уверены? Его невозможно восстановить, если вы удалите.",
                                          reply_markup=inline_kb.delete_bot_confirmation())
        else:
            await query.answer("У вас нет бота.", show_alert=True)
    elif callback_data.action == "confirmation":
        if callback_data.confirm:
            await query.message.edit_reply_markup()
            await query.answer("Запрос отправлен администратору", show_alert=True)
            users = await shortcuts.get_bot_users_count(bot_in_db)
            text = (f"Запрос на удаление бота:\n"
                    f"Админ: {html.link(query.from_user.full_name, f'tg://user?id={query.from_user.id}')}\n"
                    f"Бот: @{bot_in_db.username}\n"
                    f"Пользователи: {users}")
            bot = Bot.get_current()
            await bot.send_message(settings.ADMIN, text, reply_markup=inline_kb.send_delete_request(query.from_user.id))
        else:
            await query.message.edit_text(strings.CANCELLED)


@main_bot_router.callback_query(callback_datas.DeleteBotRequest.filter())
@flags.rate_limit(key="delete_request")
async def delete_bot_request(query: types.CallbackQuery, callback_data: callback_datas.DeleteBotRequest):
    bot_db = await shortcuts.get_user_bot(callback_data.bot_admin)
    if callback_data.action == "confirm":
        try:
            await bot_db.delete()
            try:
                async with Bot(bot_db.token, session=bot_session).context(auto_close=False) as bot:
                    await bot.delete_webhook()
            except (TelegramBadRequest, TelegramUnauthorizedError, TelegramForbiddenError):
                pass
            Bot.set_current(main_bot)
            await query.answer("Бот удален", show_alert=True)
            await query.message.edit_reply_markup()
            with suppress(TelegramForbiddenError):
                await main_bot.send_message(callback_data.bot_admin, "Бот удален ✅")
        except (TelegramBadRequest, TelegramBadRequest):
            Bot.set_current(main_bot)
            await query.answer(strings.ERROR)
    elif callback_data.action == "cancel":
        await query.message.edit_reply_markup()
