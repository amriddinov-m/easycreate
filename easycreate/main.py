import sentry_sdk
import uvicorn
from aiogram import Bot
from fastapi import FastAPI, BackgroundTasks, Body, Response, status
from tortoise import Tortoise

from api.api import api_router
from clientbot.handlers import client_bot_router
from config import settings, TORTOISE_ORM
from helpers.jobs import scheduler
from loader import dp, close_sessions, main_bot, bot_session, client_bot
from mainbot.handlers import main_bot_router

sentry_sdk.init(
    "https://14efef8f204b4007b0cd5ab80b7f72a5@o1263169.ingest.sentry.io/6442679",
    traces_sample_rate=1.0
)

app = FastAPI()
app.include_router(api_router)


@app.on_event("startup")
async def on_startup():
    webhook_url = settings.WEBHOOK_URL.format(token=main_bot.token)
    client_webhook_url = settings.WEBHOOK_URL.format(token=client_bot.token)
    webhook_info = await main_bot.get_webhook_info()
    client_webhook_info = await client_bot.get_webhook_info()

    if webhook_info.url != webhook_url:
        await main_bot.set_webhook(webhook_url, allowed_updates=settings.USED_UPDATE_TYPES)
    if client_webhook_info.url != client_webhook_url:
        await client_bot.set_webhook(client_webhook_url, allowed_updates=settings.USED_UPDATE_TYPES)
    await Tortoise.init(
        config=TORTOISE_ORM
    )
    dp.include_router(main_bot_router)
    dp.include_router(client_bot_router)
    scheduler.start()


@app.on_event("shutdown")
async def on_shutdown():
    await Tortoise.close_connections()
    await close_sessions()
    scheduler.remove_all_jobs()
    scheduler.shutdown()


async def feed_update(token, update):
    print("here")
    async with Bot(token, bot_session, parse_mode="HTML").context(auto_close=False) as bot_:
        await dp.feed_raw_update(bot_, update)


@app.post(settings.WEBHOOK_PATH, include_in_schema=False)
async def telegram_update(token: str, background_tasks: BackgroundTasks,
                          update: dict = Body(...)) -> Response:
    background_tasks.add_task(feed_update, token, update)
    return Response(status_code=status.HTTP_202_ACCEPTED)


if __name__ == '__main__':
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        log_level="error",
        workers=1
    )
