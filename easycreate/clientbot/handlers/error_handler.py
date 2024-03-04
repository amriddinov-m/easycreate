import logging
from typing import Any

from aiogram.dispatcher.handler import ErrorHandler

from loader import client_bot_router

logger = logging.getLogger()


@client_bot_router.errors()
class MyHandler(ErrorHandler):
    async def handle(self) -> Any:
        logger.exception(
            "Cause unexpected exception %s: %s",
            self.exception_name,
            self.exception_message
        )