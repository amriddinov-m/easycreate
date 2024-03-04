import logging
from random import randint

from aiogram import flags, types
from aiogram.dispatcher.fsm.context import FSMContext

from config import settings
from loader import main_bot_router
from mainbot import shortcuts, strings
from mainbot.data import states
from config import settings
from utils.aaio.AAIO import AAIO
from mainbot.keyboards import inline_kb, reply_kb
from loader import main_bot
from uuid import uuid4


logger = logging.getLogger()


@main_bot_router.callback_query(text="payout")
@flags.rate_limit(key="payout")
async def payout(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer("Выберите один из этих способов выплаты 👇",
                                reply_markup=reply_kb.fowpay_payout_methods())
    await state.set_state(states.Payout.method)


@main_bot_router.message(state=states.Payout.method)
@flags.rate_limit(key="choose-fowpay-method")
async def choose_method(message: types.Message, state: FSMContext):
    
    method = message.text
    # for item in LAVA_METHOD_MAIN:
    #     if item['name'] == method:
    #         min = int(item['min'])
    #         # сделать коммиссию
    #         user = await shortcuts.get_user(message.from_user.id)
    #         if user.balance < min:
    #             await message.answer("⛔️ Для такого перевода у вас недостаточно средств!\r\n"
    #                                  f"Минимальная сумма выплаты {min}₽")
    #         else:
    #             await state.set_state(states.Payout.amount)
    #             await state.update_data(method=item["name"], comm=min)
    #             await state.update_data(method_code=f"{item['code']}_payoff", comm=min)
    #             await message.answer(
    #                 f"Минимальная сумма выплаты {min}₽\n"
    #                 #f"Процентная ставка: {comm_in_percent}% + {dop_com_in_rub}₽\n\n"
    #                 f"💰 Баланс: {user.balance:.2f}₽\n💸 Введите необходимую сумму для снятия:\n",
    #                 reply_markup=reply_kb.cancel()
    #             )
    #         break
    aaio = AAIO(settings.AAIO_ID, settings.AAIO_SECRET_1, settings.AAIO_SECRET_2, settings.AAIO_KEY)
    methods = aaio.get_payout_methods()
    payout_method = methods.get_method(method)
    if payout_method:
        user = await shortcuts.get_user(message.from_user.id)
        commision = payout_method.commission_percent
        min = payout_method.min / 100 * commision + payout_method.min
        if user.balance < min:
            await message.answer("⛔️ Для такого перевода у вас недостаточно средств!\r\n"
                                    f"Минимальная сумма выплаты {min}₽")
        else:
            await state.set_state(states.Payout.amount)
            await state.update_data(method=payout_method.name, comm=min)
            await state.update_data(method_code=payout_method.code, comm=min)
            await message.answer(
                f"Выплата может производиться в течении 5 часов.\n"
                f"Минимальная сумма выплаты {min}₽\n"
                #f"Процентная ставка: {comm_in_percent}% + {dop_com_in_rub}₽\n\n"
                f"💰 Баланс: {user.balance:.2f}₽\n💸 Введите необходимую сумму для снятия:\n",
                reply_markup=reply_kb.cancel()
            )
        return    
    else:
        await message.answer("Неверный способ выплаты. Выберите из списка ниже")


# Withdraw amount
@main_bot_router.message(state=states.Payout.amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer(strings.NOT_DIGIT)
        return
    data = await state.get_data()
    comm = data['comm']
    if amount < comm:
        await message.answer(f"Минимальная сумма выплаты {comm}₽\n")
        return
    else:
        user = await shortcuts.get_user(message.from_user.id)
        if user.balance >= amount:
            name = data["method"]
            await state.update_data(amount=amount)
            await state.set_state(states.Payout.wallet)
            await message.answer(f"Введите номер {name} ")
        else:
            await message.answer("⛔️ Недостаточно на балансе")
            return


@main_bot_router.message(state=states.Payout.wallet)
async def withdraw(message: types.Message, state: FSMContext):
    wallet = message.text.replace(" ", "")
    data = await state.get_data()
    amount = data['amount']
    method = data['method']
    await state.update_data(wallet=wallet)
    await message.answer(
        "🔎 Пожалуйста перепроверьте информацию еще раз:\n\n"
        f"🤑 Сумма перевода: {amount} ₽\n"
        f"💳 Номер кошелька: {wallet}\n"
        f"💸 Способ вывода: {method}",
        reply_markup=reply_kb.withdraw_confirmation()
    )
    await state.set_state(states.Payout.confirmation)


@main_bot_router.message(state=states.Payout.confirmation)
@flags.rate_limit(key="withdraw_confirmation")
async def withdraw_confirmation(message: types.Message, state: FSMContext):
    match message.text:
        case "Перевести":
            try:
                data = await state.get_data()
                await state.clear()
                amount = data.get('amount')
                wallet = data.get('wallet')
                method_code = data.get('method_code')
                order = f"{uuid4()}"
                user = await shortcuts.get_user(message.from_user.id)
                if user.balance < amount:
                    await message.answer("⛔️ Недостаточно на балансе")
                    return
                
                amount = data.get('amount')
                wallet = data.get('wallet')
                method_code = data.get('method_code')

                user = await shortcuts.get_user(message.from_user.id)
                id = await shortcuts.save_payout(randint(10000, 999999999), wallet, float(amount), user, method_code)
                bot = await shortcuts.get_user_bot(user.uid)
                user.balance = user.balance - float(amount)
                await user.save()
                await message.answer(f"Заявка оставлена. ", reply_markup=reply_kb.main_menu())
                u = await user.user
                await main_bot.send_message(settings.ADMIN, f"Клиент: @{u.username} )\r\nБот: @{bot.username}\r\nСумма: {amount}\r\nМетод: {method_code}", 
                                            reply_markup=inline_kb.admin_yes_no(id))                 
                
                # lava = LavaAPI(settings.LAVA_SHOP_ID, settings.LAVA_KEY_SECRET, settings.LAVA_KEY_STILL, payout_webhook=f"{settings.HOST}/client-bot/payouts/lava")
                # lava.generate_payout(amount, order, method_code, wallet)
                # id = await shortcuts.save_payout(order, wallet, float(amount), user, method_code)
                # user.balance -= float(amount)
                # await user.save()                
                # u = await user.user
                # bot = await shortcuts.get_user_bot(u.uid)
                # await main_bot.send_message(
                #     chat_id=settings.ADMIN,
                #     # chat_id=1265627599,
                #     text=f"Новый запрос на вывод\nКлиент: @{u.username}\nСумма: {amount}₽\nКошелек: {wallet}\nБот: @{bot.username}",
                #     reply_markup=inline_kb.admin_yes_no(id)
                # )
                # await message.answer(f"Заявка оставлена. ", reply_markup=reply_kb.main_menu())
            except Exception as e:
                logger.error(e)
                await message.answer(
                    text=strings.ERROR,
                    reply_markup=reply_kb.main_menu()
                )
        case _:
            await message.answer(strings.CANCELLED, reply_markup=reply_kb.main_menu())
            await state.clear()
