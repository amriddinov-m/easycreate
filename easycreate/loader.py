from typing import Union, Dict, Any

from aiogram import Dispatcher, Bot, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.dispatcher.filters import BaseFilter
from aiogram.dispatcher.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.dispatcher.webhook.security import IPFilter
from redis.asyncio.client import Redis

from clientbot.utils.middlewares import CheckSubscription
from config import settings
from utils.middlewares import ThrottlingMiddleware
from utils.session import ClientSession

redis = Redis.from_url(url="redis://localhost", db=1)
storage = RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(with_bot_id=True))

bot_session = AiohttpSession()
client = ClientSession()
main_bot = Bot(settings.BOT_TOKEN, session=bot_session, parse_mode="HTML")
client_bot = Bot(settings.CLIENT_BOT_TOKEN, session=bot_session, parse_mode="HTML")

dp = Dispatcher(storage=storage)
dp.message.middleware(ThrottlingMiddleware())
dp.callback_query.middleware(ThrottlingMiddleware())

ip_filter = IPFilter()

client_bot_router = Router(name="clientbot")
main_bot_router = Router(name="mainbot")


class IsClientBot(BaseFilter):
    async def __call__(self, event, bot: Bot) -> Union[bool, Dict[str, Any]]:
        return client_bot == bot


class IsMainBot(BaseFilter):
    async def __call__(self, event, bot: Bot) -> Union[bool, Dict[str, Any]]:
        return main_bot == bot


for event_name, observer in client_bot_router.observers.items():
    observer.filter(IsClientBot())

for event_name, observer in main_bot_router.observers.items():
    observer.filter(IsMainBot())

client_bot_router.message.middleware(CheckSubscription())
client_bot_router.callback_query.middleware(CheckSubscription())


async def close_sessions():
    await redis.close()
    await bot_session.close()
    await main_bot.session.close()
    await client_bot.session.close()
