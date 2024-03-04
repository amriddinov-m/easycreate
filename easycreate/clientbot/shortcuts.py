import asyncio
import itertools
import json
from datetime import datetime, timezone
from datetime import timedelta
from math import floor
from typing import Union, Optional

import requests
from aiogram import types, Bot
from tortoise.transactions import in_transaction

from config import settings
from db import models
from db.items import OrderNumberResponse
from db.models import MainBotUser
from loader import redis
from smsactivate.api import SMSActivateAPI
from loader import bot_session
from mainbot.shortcuts import update_user_balance


async def get_bot():
    return await models.Bot.filter(token=Bot.get_current().token).select_related("owner").first()


async def get_bot_owner():
    current_bot = Bot.get_current()
    return await models.MainBotUser.filter(bots__token=current_bot.token).first()


async def get_all_bots():
    return models.Bot.all()


async def get_all_users(bot_admin: int):
    queryset = models.ClientBotUser.filter(bot__owner__uid=bot_admin)
    return await queryset, await queryset.count()


async def get_users_ids(bot_admin: int):
    return await models.ClientBotUser.filter(bot__owner__uid=bot_admin).values_list("uid", flat=True)


async def get_all_users_count():
    bot = Bot.get_current()
    return await models.ClientBotUser.filter(bot__token=bot.token).count()


async def get_un_bill():
    return await models.BillHistory.filter(status=models.BillStatus.WAITING).select_related("user", "user__bot")


async def finish_all_un_bill():
    await models.BillHistory.filter(status=None).select_related("user", "user__bot").update(
        status=models.BillStatus.PAID)


async def get_new_users_count():
    bot = Bot.get_current()
    today = datetime.now(tz=timezone.utc)
    return await models.ClientBotUser.filter(
        bot__token=bot.token,
        created_at__year=today.year,
        created_at__month=today.month,
        created_at__day=today.day
    ).count()


async def save_user(u: types.User, inviter: models.ClientBotUser = None):
    bot = await get_bot()
    user = await models.User.filter(uid=u.id).first()
    if not user:
        user = await models.User.create(
            uid=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
        )
    client_user = await models.ClientBotUser.create(
        uid=u.id,
        user=user,
        bot=bot,
        inviter=inviter
    )
    return client_user


async def get_main_bot_user(uid: int):
    return await models.MainBotUser.filter(uid=uid).first()


async def get_user(uid: int):
    bot = Bot.get_current()
    return await models.ClientBotUser.filter(uid=uid, bot__token=bot.token).first()


async def get_users(**kwargs):
    queryset = models.ClientBotUser.filter(**kwargs)
    return await queryset, await queryset.count()


async def reward_inviter(inviter: models.ClientBotUser):
    async with in_transaction():
        inviter.balance += 0.25
        inviter.referral_count += 1
        await inviter.save()
        await models.BalanceHistory.create(
            amount=0.25,
            balance=inviter.balance,
            type_name=models.BalanceHistory.TypeName.CHARGE,
            source=models.RefillSource.REFERRAL,
            client_bot_user=inviter
        )


async def create_order(user: models.ClientBotUser, calculated_price: float, order_id: int, profit: float,
                       bot_admin_profit: float, country: str, country_code: str, operator: str, product: str,
                       phone: str, price: str):
    order_created_at = datetime.now()
    order = await models.Order.create(
        order_id=order_id, user=user, calculated_price=calculated_price, profit=profit,
        receive_code="", receive_status="wite", bot_admin_profit=bot_admin_profit, country=country,
        country_code=country_code, operator=operator, product=product, phone=phone, price=price,
        order_created_at=order_created_at,
    )
    return order


async def get_order(order_id: int, **kwargs):
    return await models.Order.filter(order_id=order_id, **kwargs).select_related("user__bot__owner").first()


async def get_order_history(uid: int, page: int = 1):
    offset = settings.HISTORY_LIMIT * (page - 1)
    user = await get_user(uid)
    queryset = models.Order.filter(user=user, receive_status="received")
    return await queryset.limit(settings.HISTORY_LIMIT).offset(offset).order_by("-id"), await queryset.count()


async def clear_all():
    await models.Order.filter().update(receive_status="wite")


async def get_not_finished_orders():
    return await models.Order.filter(receive_status="wite")


async def get_balance_history(uid: int, page: int = 1):
    offset = settings.HISTORY_LIMIT * (page - 1)
    client_bot_user = await get_user(uid)
    queryset = models.BalanceHistory.filter(client_bot_user=client_bot_user).order_by("-id")
    return await queryset.limit(settings.HISTORY_LIMIT).offset(offset), await queryset.count()


async def create_bill(user: models.ClientBotUser, bill_id: str, amount: float, comment: str = None):
    bill = await models.BillHistory.create(
        user=user,
        bill_id=bill_id,
        amount=amount,
        comment=comment,
        status=models.BillStatus.WAITING
    )
    return bill


async def get_bill(bill_id: str):
    return await models.BillHistory.filter(bill_id=bill_id).select_related("user", "user__bot").first()


async def earned():
    bot = Bot.get_current()
    orders = await models.Order.filter(user__bot__token=bot.token)
    total_earned = 0
    for order in orders:
        total_earned += order.bot_admin_profit
    return f"{total_earned:.2f}"


async def earned_today():
    bot = Bot.get_current()
    today = datetime.now(timezone.utc)
    orders = await models.Order.filter(user__bot__token=bot.token, created_at__year=today.year,
                                       created_at__month=today.month,
                                       created_at__day=today.day)
    total_earned = 0
    for order in orders:
        total_earned += order.bot_admin_profit
    return f"{total_earned:.2f}"


async def ordered_today():
    bot = Bot.get_current()
    today = datetime.now(timezone.utc)
    orders = await models.Order.filter(user__bot__token=bot.token, created_at__year=today.year,
                                       created_at__month=today.month,
                                       created_at__day=today.day).count()
    return orders


async def change_balance(user: Union[int, models.ClientBotUser], amount: float, type_name: str, source: str):
    bot = Bot.get_current()
    if isinstance(user, int):
        user = await models.ClientBotUser.filter(uid=user, bot__token=bot.token).first()
    user.balance += amount
    await user.save()
    await models.BalanceHistory.create(
        client_bot_user=user,
        balance=user.balance,
        amount=amount,
        type_name=type_name,
        source=source
    )


async def get_subscription_chats(bot: models.Bot):
    chats = await models.SubscriptionChat.filter(bot=bot).order_by("-id")
    return chats


async def get_subscription_chat(bot: models.Bot, chat_id: Union[int, str]):
    return await models.SubscriptionChat.filter(bot=bot, uid=chat_id).first()


async def add_subscription_chat(bot: models.Bot, chat: types.Chat, invite_link: types.ChatInviteLink):
    async with in_transaction():
        await models.SubscriptionChat.create(
            bot=bot,
            title=chat.title or chat.first_name,
            uid=chat.id,
            username=chat.username,
            type=chat.type,
            invite_link=invite_link.invite_link
        )
        bot.subscription_chats_changed_at = datetime.now(timezone.utc)
        await bot.save()


async def get_countries(page: int = 1, country_code: str = None, search_key: str = None):
    states_url = f'{settings.SMS_ACTIVATE_URL}getTariffs.php?apikey={settings.SMS_ACTIVATE_TOKEN}'
    states = requests.get(states_url).json()
    states_list = [{'id': key, 'name': states['countries'][key]['name'], 'code': states['countries'][key]['code']} for
                   key in states['countries']]
    # for key in states:
    #     states_list.append({
    #         'id': key,
    #         'name': states[key]['name'],
    #         'code': states[key]['code'],
    #     })
    # _redis_key = "smsActivate:countries"
    limit = 15
    offset = limit * (page - 1)
    return states_list[offset:limit * page], len(states_list)
    # countries = await redis.get(_redis_key)
    # if countries:
    #     countries = json.loads(countries)
    # else:
    #     lock = asyncio.Lock()
    #     async with lock:
    #         sms = SMSActivateAPI(settings.SMS_ACTIVATE_TOKEN)
    #         countries: dict = sms.getCountries()
    #         with open("countries.json", "wt", encoding="utf8") as f:
    #             f.write(json.dumps(countries, ensure_ascii=False, indent=4))
    #         countries = [{key: value} for key, value in countries.items()]
    #         await redis.set(_redis_key, json.dumps(countries), ex=86400)
    # return countries[offset:limit * page], len(countries)
    # if country_code:
    #     for country_ in countries:
    #         key = tuple(country_.keys())[0]
    #         if tuple(country_[key]['iso'].keys())[0] == country_code:
    #             return country_[key]
    # elif search_key:
    #     choices = {}
    #     for country_ in countries:
    #         key = tuple(country_.keys())[0]
    #         choices[tuple(country_[key]['iso'].keys())[0]] = (
    #             country_[key]['text_en'], country_[key]['text_ru'], tuple(country_[key]['iso'].keys())[0])
    #     return process.extractBests(search_key, choices, scorer=fuzz.WRatio, score_cutoff=70)
    # return countries[offset:limit * page], len(countries)


def get_operators(country: dict):
    country.pop('iso')
    country.pop('prefix')
    country.pop('text_ru')
    country.pop('text_en')
    return country


async def get_price(country: str, service: str) -> float:
    sms = SMSActivateAPI(settings.SMS_ACTIVATE_TOKEN)
    response = sms.getPrices(service, country)
    return response[country][service]['cost']


async def get_products(country: str, operator: str, page: int = 1, product: str = None, search_key: str = None):
    limit = 15
    offset = limit * (page - 1)
    sa = SMSActivateAPI(settings.SMS_ACTIVATE_TOKEN)
    response = sa.getRentServicesAndCountries(operator=operator, country=country)
    with open("products.json", "wt", encoding="utf8") as f:
        f.write(json.dumps(response, ensure_ascii=False, indent=4))
    if "status" in response and response["status"] == "error":
        raise Exception("Этого оператора временно нельзя выбрать")
    products: dict = response["services"]
    products = [{key: value} for key, value in products.items()]
    # if product:
    #     for product_ in products:
    #         key = list(product_.keys())[0]
    #         if product == key:
    #             return product_[key]
    # elif search_key:
    #     keys = []
    #     for product_ in products:
    #         keys.append(list(product_.keys())[0])
    #     return process.extractBests(search_key, keys, scorer=fuzz.WRatio, score_cutoff=70)
    return products[offset:limit * page], len(products)


def round_number(number: float):
    n = floor(number)
    if number - n >= 0.5:
        return n + 1
    else:
        return n + 0.5


def get_product(products: list, service: str) -> dict:
    """"""
    for product_dict in products:
        product_dict: dict = product_dict
        for key, value in product_dict.items():
            if key == service:
                return value
    return {}


async def calculate_price(uid: int, product_price: float, round_: bool = True):
    bot = await get_bot()
    bot_owner: MainBotUser = bot.owner
    price = product_price * 2
    bot_percent = 0
    if bot_owner.uid != uid:
        bot_percent = price * bot.percent / 100
        price += bot_percent
    if round_:
        price = round_number(price)
    profit = price - bot_percent - product_price
    return price, profit, bot_percent


class Payouts:
    _redis_key = "easycreate:fowpay:payouts"

    @classmethod
    async def _set(cls, payouts: list):
        await redis.set(cls._redis_key, json.dumps(payouts))

    @classmethod
    async def get(cls) -> list:
        payouts = await redis.get(cls._redis_key)
        payouts = None
        if not payouts:
            payouts = []
            await cls._set(payouts)
        return payouts

    @classmethod
    async def get_first(cls) -> Optional[str]:
        payouts = await cls.get()
        if payouts:
            return payouts[0]
        return

    @classmethod
    async def add(cls, payout_id: str, user_id: int):
        payouts = await cls.get()
        if payout_id not in itertools.chain(*[i.items() for i in payouts]):
            payouts.append({payout_id: user_id})
            await cls._set(payouts)

    @classmethod
    async def delete(cls, payout_id: str):
        payouts = list(filter(lambda payout: payout_id not in payout, await cls.get()))
        await cls._set(payouts)


def get_num(text: str) -> str:
    a = text.split(":")
    b = a[1] if len(a) > 0 else a
    return b


async def delete_order(order_id: int):
    await models.Order.filter(order_id=order_id).delete()


async def change_order_details(order_id: int, receive_code: str, receive_status: str):
    order = await get_order(order_id)
    order.receive_code = receive_code
    order.receive_status = receive_status
    await order.save()


async def change_order_phone(order_id: int, new_order_id: int, new_phone: str):
    order = await get_order(order_id)
    order.order_id = new_order_id
    order.phone = new_phone
    await order.save()


async def check_order(order_id: int) -> str or None:
    order = await get_order(order_id)
    sa = SMSActivateAPI(settings.SMS_ACTIVATE_TOKEN)
    response = sa.getFullSms(id=order.order_id)
    if f"{response}" == "STATUS_WAIT_CODE":
        return "wait"
    if not isinstance(response, dict):
        return f"{response}"
    else:
        return None


async def get_phone(user_id: int, country: str, product: str, operator: str) -> OrderNumberResponse or None:
    sms = SMSActivateAPI(settings.SMS_ACTIVATE_TOKEN)
    while True:
        response = sms.getNumberV2(country=country, service=product, operator=operator)
        with open("response.txt", "wt", encoding="utf8") as f:
            f.write(f"{country=} {product=} {operator=}" + json.dumps(response, ensure_ascii=False, indent=4))
        if isinstance(response, dict) and 'activationId' in response and 'phoneNumber' in response:
            order_id = response['activationId']
            phone = response['phoneNumber']
            if not await has_phone_in_block(user_id, phone, order_id):
                return OrderNumberResponse(order_id, phone)
            else:
                cancel_order(order_id)
        else:
            break
    return None


async def finish_order(order_id: int):
    # Изменить деньни из заморозки в баланс
    order = await get_order(order_id)
    user: models.ClientBotUser = await order.user
    bot: models.Bot = await user.bot
    owner: models.MainBotUser = await bot.owner
    async with Bot(bot.token, session=bot_session).context(auto_close=False) as b:
        b: Bot = b
        await update_user_balance(owner, order.profit)
        await b.send_message(owner.uid, f"Клиент сделал заказ на {order.price} рублей. Вам начислено: {order.profit}")
    change_order_status(order_id, 6)


async def cancel_order(order_id: int):
    # Убрать деньни из заморозки
    change_order_status(order_id, 8)


async def cancel_order_and_finish(order_id: int):
    # Убрать деньни из заморозки
    order = await get_order(order_id)
    user: models.ClientBotUser = await order.user
    await change_balance(user.uid, order.price, "charge", order.product)
    change_order_status(order_id, 8)


def change_order_status(order_id: int, status: int):
    sms = SMSActivateAPI(settings.SMS_ACTIVATE_TOKEN)
    sms.setStatus(order_id, status=status)


async def add_phone_to_ban(user_uid: int, phone: str, service: str):
    user = await get_user(user_uid)
    await models.BanModel.create(
        user=user,
        service=service,
        phone=phone
    )


async def has_phone_in_block(user_uid: int, phone: str, service: str):
    user = await get_user(user_uid)
    ban = await models.BanModel.filter(user=user, phone=phone, service=service)
    return len(ban) > 0
