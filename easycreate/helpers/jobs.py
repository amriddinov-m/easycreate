import logging
from contextlib import suppress
# from py_lava_api.LavaAPI import LavaAPI

from config import settings, scheduler
from clientbot import shortcuts, strings

from aiogram import Bot
from db.models import ClientBotUser, Bot as BotModel
from loader import bot_session

# scheduler.add_job(check_orders, trigger=IntervalTrigger(minutes=1, timezone=timezone.utc))
# scheduler.add_job(check_payout, trigger=IntervalTrigger(minutes=1, timezone=timezone.utc))

# scheduler.add_job(check_payment, trigger=IntervalTrigger(
#     minutes=3, timezone=timezone.utc))  # 5
