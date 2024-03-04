import asyncio
import logging
import random
import time
from datetime import datetime, timezone
from typing import Union

from aiogram import Bot
from aiogram import types
from aiogram.exceptions import TelegramUnauthorizedError, TelegramNetworkError, TelegramAPIError
from aiohttp import ContentTypeError
from tortoise.transactions import in_transaction

from config import settings
from db import models
from helpers.exceptions import BadRequest
from loader import client, bot_session
from mainbot import strings

logger = logging.getLogger()


async def get_bot(**kwargs):
    return await models.Bot.filter(**kwargs).first()


async def save_bot(token: str, uid: int, percent: int, bot_username: str):
    user = await get_user(uid)
    await models.Bot.create(
        owner=user,
        token=token,
        percent=percent,
        username=bot_username
    )


async def save_user(u: types.User):
    user = await models.User.filter(uid=u.id).first()
    if not user:
        user = await models.User.create(
            uid=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
        )
    main_bot_user = await models.MainBotUser.create(
        uid=u.id,
        user=user
    )
    return main_bot_user


async def get_user(uid: int):
    return await models.MainBotUser.filter(uid=uid).first()


async def get_all_users():
    return await models.User.all().order_by('id')


async def get_bots():
    return await models.Bot.filter(unauthorized=False).select_related("owner")


async def get_all_users_count():
    return await models.User.all().count()


async def get_all_users_count_by_month(year: int = None, month: int = None):
    today = datetime.today().replace(tzinfo=settings.timezone)
    if year is None:
        year = today.year
    if month is None:
        month = today.month
    return await models.User.filter(created_at__year=year, created_at__month=month).count()


async def get_bot_users():
    return await models.MainBotUser.all().order_by('id')


async def users_count():
    return await models.MainBotUser.all().count()


async def bots_count():
    return await models.Bot.all().count()


async def get_user_bot(uid: int):
    user = await get_user(uid)
    return await models.Bot.filter(owner=user).first()


async def get_bot_percent(uid: int):
    bot = await get_user_bot(uid)
    if bot:
        return bot.percent


async def get_frozen_balance(user: models.MainBotUser):
    bot = await models.Bot.filter(owner=user).first()
    orders = await models.Order.filter(user__bot=bot)
    balance = 0
    for order in orders:
        balance += order.bot_admin_profit
    return balance


async def increase_referral(uid: int):
    user = await get_user(uid)
    if user:
        await user.update_from_dict({'referral_count': user.referral_count + 1}).save()
        return True
    return False


async def referral_count(uid: int):
    user = await get_user(uid)
    if user:
        return user.referral_count
    return


async def user_balance(uid: int):
    user = await get_user(uid)
    if user:
        return user.balance
    return


async def transfer_money(uid: int, amount: float):
    amount = prettify_float(amount)
    user = await get_user(uid)
    if user:
        user.referral_balance = user.referral_balance - amount
        user.balance = user.balance + amount
        await user.save()
        return True
    return


async def referral_balance(uid: int):
    user = await get_user(uid)
    return user.referral_balance


async def edit_bot_percent(uid: int, percent: int):
    bot = await get_user_bot(uid)
    bot.percent = percent
    await bot.save()


async def update_user_balance(user: Union[models.MainBotUser, int], amount):
    if isinstance(user, int):
        user = await get_user(user)
    user.balance = user.balance + amount
    await user.save()


async def new_users():
    today = datetime.now(timezone.utc)
    return await models.User.filter(created_at__year=today.year, created_at__month=today.month,
                                    created_at__day=today.day).count()


async def ordered_today():
    today = datetime.now(timezone.utc)
    return await models.Order.filter(created_at__year=today.year, created_at__month=today.month,
                                     created_at__day=today.day).count()


async def earned_today():
    today = datetime.now(timezone.utc)
    orders = await models.Order.filter(created_at__year=today.year, created_at__month=today.month,
                                       created_at__day=today.day)
    profit = 0
    for order in orders:
        profit += order.profit
    return f"{profit:.2f}"


async def monthly_earning(year: int = None, month: int = None):
    today = datetime.now(timezone.utc)
    if year is None:
        year = today.year
    if month is None:
        month = today.month
    orders = await models.Order.filter(status="Completed", created_at__year=year, created_at__month=month)
    profit = 0
    for order in orders:
        profit += order.profit
    return f"{profit:.2f}"


async def annually_earning():
    today = datetime.now(timezone.utc)
    orders = await models.Order.filter(status="FINISHED", created_at__year=today.year)
    profit = 0
    for order in orders:
        profit += order.profit
    return f"{profit:.2f}"


async def earned():
    orders = await models.Order.filter(receive_status="received")
    profit = 0
    for order in orders:
        profit += order.profit
    return f"{profit:.2f}"


async def get_bot_by_username(bot_username: str):
    return await models.Bot.filter(username__iexact=bot_username).first()


async def get_bot_user(bot: Union[int, models.Bot], uid: int):
    user = await models.ClientBotUser.filter(bot=bot, uid=uid).first()
    return user


async def get_bot_users_count(bot: models.Bot):
    return await models.ClientBotUser.filter(bot=bot).count()


async def update_client_balance(id_: int, sum_: float):
    user = await models.ClientBotUser.get(id=id_)
    user.balance += sum_
    await user.save()
    return user.balance


async def change_balance(user: Union[int, models.ClientBotUser], amount: float, type_name: str, source: str):
    if isinstance(user, int):
        user = await models.ClientBotUser.get(id=user)
    async with in_transaction():
        user.balance += amount
        await user.save()
        await models.BalanceHistory.create(
            client_bot_user=user,
            balance=user.balance,
            amount=amount,
            type_name=type_name,
            source=source
        )
    return user


async def send_p2p(comment, to_qw, sum_p2p):
    headers = {'content-type': 'application/json', 'authorization': 'Bearer ' + settings.QIWI_TOKEN,
               'User-Agent': 'Android v3.2.0 MKT', 'Accept': 'application/json'}
    payload = {
        "id": str(int(time.time() * random.randint(1000, 9999))),
        "sum": {
            "amount": sum_p2p,
            "currency": "643"
        },
        "paymentMethod": {
            "type": "Account",
            "accountId": "643"
        },
        "comment": comment,
        "fields": {
            "account": to_qw
        }
    }

    async with client.session.post('https://edge.qiwi.com/sinap/api/v2/terms/99/payments', json=payload,
                                   headers=headers) as r:
        try:
            response = await r.json()
        except ContentTypeError:
            text = await r.text()
            logger.error(text)
            raise Exception(text)
        if r.status == 200:
            if response["transaction"]["state"]["code"] != "Accepted":
                raise Exception
            else:
                return response
        elif r.status == 400:
            raise BadRequest(message=response['message'])
        else:
            raise Exception


async def restart_bots(admin_id: int):
    main_bot = Bot.get_current()
    bots = await get_bots()
    succeeded, failed = 0, 0
    for bot_ in bots:
        try:
            async with Bot(token=bot_.token, session=bot_session).context(auto_close=False) as bot:
                url = settings.WEBHOOK_URL.format(token=bot_.token)
                await bot.set_webhook(url, allowed_updates=settings.USED_UPDATE_TYPES)
                succeeded += 1
                await asyncio.sleep(.1)
        except (TelegramUnauthorizedError, TelegramNetworkError, TelegramAPIError):
            failed += 1
    await main_bot.send_message(admin_id, strings.RESTARTING_BOTS_RESULT.format(succeeded=succeeded, failed=failed))


def prettify_float(num: float):
    return float(format(num, '.2f'))


async def save_payout(order: str, wallet: str, amount: float, user: Union[models.MainBotUser, int], method_code: str):
    if isinstance(user, int):
        user = await models.MainBotUser.filter(uid=user).first()
    res = await models.Payout.create(
        user=user,
        success="Payout created",
        payout_id=order,
        payout_wallet=wallet,
        payout_wallet_type=method_code,
        payout_amount=amount,
        payout_amount_down=amount,
        payout_commission=amount,
        payout_commission_type="payment",
        payout_status="wait",
        payout_date_success=datetime.now()
    )
    res.save()
    return res.id


async def get_payout(payout_id: int):
    return await models.Payout.filter(payout_id=payout_id).select_related("user").first()

async def get_payout_id(id: int):
    return await models.Payout.filter(id=id).select_related("user").first()

async def get_admin_bot(admin_uid: str):
    return await models.Bot.filter(owner__uid=admin_uid).first()

async def get_user_waiting_payout(user: Union[models.MainBotUser, int]):
    if isinstance(user, int):
        user = await models.MainBotUser.filter(uid=user).first()
    return await models.Payout.filter(user=user, payout_status="wait").first()


async def get_waiting_payouts():
    return await models.Payout.filter(payout_status="wait").select_related("user").order_by("id")


def calculate_commission(min_in_rub: Union[float, str], comm_in_percent: Union[float, str],
                         dop_com_in_rub: Union[float, str] = 0):
    if isinstance(min_in_rub, str):
        min_in_rub = float(min_in_rub)

    if isinstance(comm_in_percent, str):
        comm_in_percent = float(comm_in_percent)

    if isinstance(dop_com_in_rub, str):
        dop_com_in_rub = float(dop_com_in_rub)

    return round((min_in_rub + dop_com_in_rub) / (1 - comm_in_percent / 100), 2)
