from contextlib import suppress
from uuid import uuid4

from aiogram import Bot, flags
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from config import settings
from utils.cryptomus.cryptomus import Cryptomus
from utils.cryptomus.models import Currency

from clientbot import shortcuts, strings
from clientbot.data.callback_datas import (
    BalanceCallbackData,
    BalanceHistoryCallbackData
)
from clientbot.data.states import RefillAmount
from clientbot.keyboards import inline_kb, reply_kb
from loader import client_bot_router
from utils.aaio.AAIO import AAIO
from clientbot.keyboards.functs import get_cryptomus_services
from aiogram import flags
from aiogram.dispatcher.fsm.context import FSMContext

from clientbot import shortcuts, strings
from clientbot.keyboards import reply_kb

async def show_panel_input_amount(message: Message, state: FSMContext) -> None:
    """Панель для ввода сумы пополнения"""
    text = ("Вы можете пополнить сумму ниже через кнопку, либо введите желаемую сумму:\n\n"
            "Пример: 100\n")
    await message.answer(
        text,
        reply_markup=reply_kb.amount_kb()
    )
    await state.set_state(RefillAmount.amount)
    
async def show_panel_input_amount(message: Message, state: FSMContext) -> None:
    """Панель для ввода сумы пополнения"""
    text = ("Вы можете пополнить сумму ниже через кнопку, либо введите желаемую сумму:\n\n"
            "Пример: 100\n")
    await message.answer(
        text,
        reply_markup=reply_kb.amount_kb()
    )
    await state.set_state(RefillAmount.amount)

@client_bot_router.callback_query(BalanceCallbackData.filter())
@flags.rate_limit(key="balance_cd")
async def balance_cd(query: CallbackQuery, state: FSMContext, callback_data: BalanceCallbackData):
    match callback_data.action:
        case "history":
            items, count = await shortcuts.get_balance_history(query.from_user.id)
            text = strings.print_balance_history(items)
            if text is None:
                await query.answer(strings.NOTHING_FOUND, show_alert=True)
            else:
                await query.answer()
                await query.message.edit_text(text, reply_markup=inline_kb.balance_history_kb(count))

        case "refill":
            with suppress(TelegramBadRequest):
                await query.message.edit_reply_markup()
            await show_panel_input_amount(query.message, state)


@client_bot_router.message(state=RefillAmount.amount)
@flags.rate_limit(key="refill_amount")
async def refill_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("Баланс пользователя должен быть в цифрах")
    else:
        text = (
            f"Текущая сумма пополнения: {amount}\n\n"
            "Выберите один из способов пополнения\n"
        )
        await message.answer(text, reply_markup=reply_kb.refill_balance_methods())
        await state.set_state(RefillAmount.method)
        await state.update_data(amount=amount)


@client_bot_router.message(state=RefillAmount.method)
@flags.rate_limit(key="refill-amount-state")
async def refill_method(message: Message, state: FSMContext, bot: Bot):
    method = message.text
    if method == "Криптовалюты":
        await message.answer("Выберите криптовалюту", reply_markup=reply_kb.refill_crypto_balance_methods())
        await state.set_state(RefillAmount.crypto)
        return
    # for payment in strings.LAVA_METHOD:
    #     if method == payment['name']:
    #         data = await state.get_data()
    #         amount = data['amount']
    #         min_sum = payment["min"]
    #         max_sum = payment["max"]
    #         a = float(amount)
    #         if a >= min_sum and a <= max_sum:
    #             user = await shortcuts.get_user(message.from_user.id)
    #             order_id = str(uuid4())
    #             bot_obj = await shortcuts.get_bot()
    #             await bot.send_chat_action(message.from_user.id, "typing")

    #             desc = f"Пополнение баланса в боте t.me/{bot_obj.username}"
    #             await shortcuts.create_bill(user, order_id, amount, comment=desc)
    #             url = generate_payment_url(amount, order_id)
    #             await message.answer(
    #                 text=f"🔗 Перейдите по ссылке на кнопке и оплатите ваш тариф.",
    #                 reply_markup=inline_kb.payment(
    #                     url=url, order_id=order_id
    #                 )
    #             )
    #             await state.clear()
    #             break
    #         else:
    #             await message.answer(f"Сума должна быть больше {min_sum} рублей и меньше {max_sum} рублей")
    #             await show_panel_input_amount(message, state)
    #             break
    data = await state.get_data()
    amount = data['amount']
    a = float(amount)    
    aaio = AAIO(settings.AAIO_ID, settings.AAIO_SECRET_1, settings.AAIO_SECRET_2, settings.AAIO_KEY)
    methods = aaio.get_payment_methods()
    method = methods.get_method(message.text)
    if method:
        if a >= method.min.RUB and a <= method.max.RUB:
            #check min max
            data = await state.get_data()
            amount = float(data['amount'])
            user = await shortcuts.get_user(message.from_user.id)
            order_id = str(uuid4())
            bot_obj = await shortcuts.get_bot()
            await bot.send_chat_action(message.from_user.id, "typing")
            desc = f"Пополнение баланса в боте t.me/{bot_obj.username}"
            await shortcuts.create_bill(user, order_id, amount, comment=desc)
            url = aaio.payment(amount, order_id)
            await message.answer(
                text=f"🔗 Перейдите по ссылке на кнопке и оплатите ваш тариф.\r\n"
                , reply_markup=inline_kb.payment(
                    url=url, order_id=order_id
                )
            )
            await state.clear()
        else:
            await message.answer(f"Сумма должна быть больше {method.min.RUB} рублей и меньше {method.max.RUB} рублей")
            await show_panel_input_amount(message, state)
        return          
    else:
        await message.answer("Неверный способ. Выберите из списка ниже")


@client_bot_router.callback_query(BalanceHistoryCallbackData.filter())
async def balance_history_pages(query: CallbackQuery, callback_data: BalanceHistoryCallbackData):
    match callback_data.action:
        case "paginate":
            items, count = await shortcuts.get_balance_history(query.from_user.id, page=callback_data.page)
            text = strings.print_balance_history(items)
            await query.message.edit_text(text, reply_markup=inline_kb.balance_history_kb(count, callback_data.page))
        case "page-list":
            items, count = await shortcuts.get_balance_history(query.from_user.id, page=callback_data.page)
            text = "📖 Пожалуйста, выберите страницу"
            await query.message.edit_text(text, reply_markup=inline_kb.balance_history_pages(count, callback_data.page))
        case "back":
            user = await shortcuts.get_user(query.from_user.id)
            text = strings.BALANCE.format(balance=user.balance, uid=query.from_user.id)
            await query.message.edit_text(text, reply_markup=inline_kb.balance_menu())
    await query.answer()
    
@client_bot_router.message(state=RefillAmount.crypto)
@flags.rate_limit(key="refill-amount-state")
async def refill_method(message: Message, state: FSMContext, bot: Bot):
    method = message.text
    for service in get_cryptomus_services():
        if method == f"{service.network} {service.currency}":
            min_sum = float(service.limit.min_amount)
            max_sum = float(service.limit.max_amount)
            data = await state.get_data()
            amount = data['amount']
            a = float(amount)
            if a >= min_sum and a <= max_sum:
                user = await shortcuts.get_user(message.from_user.id)
                order_id = str(uuid4())
                bot_obj = await shortcuts.get_bot()
                await bot.send_chat_action(message.from_user.id, "typing")
                desc = f"Пополнение баланса в боте t.me/{bot_obj.username}"
                await shortcuts.create_bill(user, order_id, amount, comment=desc)
                crypto = Cryptomus(settings.CRYPTOMUS_MERCHANT, settings.CRYPTOMUS_APPKEY)
                
                
                courency_result = crypto.currency(service.currency)
                amount_cur = 0
                if len(courency_result.result) == 0:
                    await message.answer("Не удалось загрузить валюты. Повторите позже")
                    await state.clear()
                for curency in courency_result.result:
                    curency: Currency = curency
                    if curency.to == "RUB":
                        amount_cur = float(curency.course)
                        break
                if amount_cur == 0:
                    await message.answer("Не удалось загрузить валюты. Повторите позже")
                    await state.clear()
                else:
                    amount = float(amount) / float(amount_cur)
                
                result = crypto.add_payment(str(amount), service.currency, order_id, network=service.network, url_callback=f"{settings.HOST}/client-bot/payments/cryptomus")
                url = result.url
                with open("cryptoPayment.txt", "a") as f:
                    f.write(f"{result.__dict__}\r\n")
                await message.answer(
                    text=f"🔗 Перейдите по ссылке на кнопке и оплатите ваш тариф.\r\n"
                    , reply_markup=inline_kb.payment(
                        url=url, order_id=order_id
                    )
                )
                await state.clear()
            else:
                await message.answer(f"Сумма должна быть больше {min_sum} рублей и меньше {max_sum} рублей")
                await show_panel_input_amount(message, state)
            return
    else:
        await message.answer("Неверный способ. Выберите из списка ниже")
        return