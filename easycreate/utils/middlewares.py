from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.flags.getter import get_flag
from aiogram.types import TelegramObject, User, CallbackQuery
from aiolimiter import AsyncLimiter
from config import DEBUG, settings


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, default_rate: int = 1.4) -> None:
        self.limiters: Dict[str, AsyncLimiter] = {}
        self.default_rate = default_rate

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        user: Optional[User] = data.get("event_from_user")
        if DEBUG and user.id not in settings.ADMIN_LIST:
            await event.answer("Бот на реконструкторе, попробуйте позже!")
            return
        real_handler: HandlerObject = data["handler"]
        throttling_flag = get_flag(real_handler, 'rate_limit')
        if throttling_flag is None:
            throttling_flag = {}
        throttling_key = throttling_flag.get('key', None)
        throttling_rate = throttling_flag.get('rate', self.default_rate)

        if not throttling_key or not user:
            return await handler(event, data)

        limiter = self.limiters.setdefault(
            f"{user.id}:{throttling_key}", AsyncLimiter(1, throttling_rate)
        )
        if limiter.has_capacity():
            async with limiter:
                return await handler(event, data)
        else:
            if isinstance(event, CallbackQuery):
                await event.answer("Не флуди! Подожди секунду!")
