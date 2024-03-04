from config import settings
from aiogram import Bot
from clientbot import shortcuts
from loader import bot_session

async def send_message(bot_token: str, uid: str, message: str):
    try:
        async with Bot(token=bot_token, session=bot_session).context(auto_close=False) as bot:
            await bot.send_message(uid, message)
        return True
    except:
        return False