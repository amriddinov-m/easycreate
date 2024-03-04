from contextlib import suppress
from typing import TYPE_CHECKING

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from fastapi import BackgroundTasks, APIRouter, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from clientbot import shortcuts, strings
from config import settings
from db.items import LavaBillItem
from db.models import BillStatus
from helpers.functions import send_message
from loader import bot_session
from utils.cryptomus.cryptomus import Cryptomus
from utils.cryptomus.models import Currency, change_dict_key, PaymentWebhook
from utils.aaio.AAIO import AAIO
from utils.aaio.models import PaymentWebhook as AAIOPaymentWebhook, PayoutWebhook as AAIOPayoutWebhook
if TYPE_CHECKING:
    from db.models import ClientBotUser, Bot as BotModel

router = APIRouter()
FOWPAY_IPS_URL = "https://fowpay.com/ips.json"


@router.get("/succeed")
async def payment_succeeded(order: str = Query(None)):
    if order:
        bill = await shortcuts.get_bill(order)
        user: ClientBotUser = bill.user
        bot: BotModel = user.bot
        return RedirectResponse(f"https://t.me/{bot.username}")
    else:
        return "Order not found"


@router.post("/aaio")
async def payok_payment(
    request: Request,
    background_tasks: BackgroundTasks,
):
    bill = await request.form()
    bill = bill._dict
    with open("aaioPayment.txt", "a") as f:
        f.write(f"{bill}\r\n")
    aaio = AAIO(settings.AAIO_ID, settings.AAIO_SECRET_1, settings.AAIO_SECRET_2, settings.AAIO_KEY)
    if 'order_id' in bill:    
        payment = AAIOPaymentWebhook(**bill)
        order = await shortcuts.get_bill(payment.order_id)
        if order.status == BillStatus.WAITING:
            user = await order.user
            bot = await user.bot        
            user.balance += order.amount
            await user.save()
            order.status = BillStatus.PAID
            await order.save()
            await send_message(bot.token, user.uid, strings.BALANCE_CHARGED.format(order.amount))
                                
@router.post("/cryptomus")
async def payok_payment(
    request: Request,
    background_tasks: BackgroundTasks,
    data_webhook: dict
):
    with open("cryptoPayment.txt", "a") as f:
        f.write(f"{data_webhook}\r\n")
    original_data = data_webhook
    crypto = Cryptomus(settings.CRYPTOMUS_MERCHANT, settings.CRYPTOMUS_APPKEY)
    sign = original_data.pop("sign")
    my_sign = crypto.gen_sign_to_check(original_data)     
    if sign != my_sign:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    data = change_dict_key(original_data, "from", "from_wallet")
    data = PaymentWebhook(**data)
    payment = await shortcuts.get_bill(data.order_id)
    # if payment.status != "WAITING" or data.status != "paid":
    if data.status not in ["paid", "paid_over", "wrong_amount", "wrong_amount_waiting"]:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    payment.status = "PAID"
    courency_result = crypto.currency(data.currency)
    amount = 0
    if len(courency_result.result) == 0:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    for curency in courency_result.result:
        curency: Currency = curency
        if curency.to == "RUB":
            amount = float(curency.course)
            break
    if amount == 0:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    else:
        payment.amount = float(data.merchant_amount) * amount
    user = await payment.user
    bot = await user.bot        
    user.balance += payment.amount
    await user.save()
    await payment.save()     
    await send_message(bot.token, user.uid, strings.BALANCE_CHARGED.format(payment.amount) + f"\r\nКурс: {amount}")
    return Response(status_code=status.HTTP_200_OK)       