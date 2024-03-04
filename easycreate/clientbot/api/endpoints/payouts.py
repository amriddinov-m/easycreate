from contextlib import suppress
import json
from typing import TYPE_CHECKING
from db import models
from utils.aaio.AAIO import AAIO
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from fastapi import BackgroundTasks, APIRouter, Request, Response
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from clientbot import shortcuts, strings
from config import settings
from db.items import LavaBillItem, LavaPayoutItem
from db.models import BillStatus
from loader import bot_session
from loader import main_bot
from mainbot.shortcuts import get_payout, get_admin_bot
from utils.aaio.models import PaymentWebhook as AAIOPaymentWebhook, PayoutWebhook as AAIOPayoutWebhook
if TYPE_CHECKING:
    from db.models import MainBotUser, Bot as BotModel

router = APIRouter()


@router.post("/aaio")
async def payok_payment(
    request: Request,
    background_tasks: BackgroundTasks,
):
    bill = await request.form()
    bill = bill._dict
    with open("aaiop.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(bill, ensure_ascii=False, indent=4))
    pay = AAIOPayoutWebhook(**bill)    
    payout = await get_payout(pay.my_id)
    user: models.MainBotUser = await payout.user    
    if pay.status == "success":
        payout = await get_payout(pay.my_id)
        user: MainBotUser = await payout.user
        if payout and payout.payout_status == "wait":
            await main_bot.send_message(
                chat_id=settings.PAYS,
                text=f"✅ Выплачено партнеру под ID: {user.id} на сумму {payout.payout_amount} р."
            )
            payout.payout_status = "success"
            await payout.save()
            async with Bot(settings.BOT_TOKEN, session=bot_session).context(auto_close=False) as b:
                with suppress(TelegramBadRequest):
                    await b.send_message(
                        chat_id=user.uid,
                        text=f"🥳 {float(payout.payout_amount)}₽ успешно переведены на счёт!"
                    )                
    return Response(status_code=200)